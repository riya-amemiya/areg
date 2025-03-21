import json
import os
import re
import argparse
from typing import List, Dict, Optional, TypedDict, Literal
from dotenv import load_dotenv
from openai import OpenAI, APIError

load_dotenv()


class I18NMessages(TypedDict):
    prompt: str
    exit_info: str
    error_message: str
    test_request: str
    result_success: str
    result_failure: str
    api_error: str
    keyboard_interrupt: str
    regex_display: str


I18N: Dict[str, I18NMessages] = {
    "ja": {
        "prompt": "正規表現を入力してください",
        "exit_info": "で終了。",
        "error_message": "正規表現が間違っているようです。もう一度入力してください。",
        "test_request": "テストして",
        "result_success": "✅ 正規表現が正しいです：",
        "result_failure": "❌ 正規表現が一致しません",
        "api_error": "APIエラーが発生しました: ",
        "keyboard_interrupt": "\n終了します。",
        "regex_display": "正規表現: {} \nテスト文字列: {} \n期待結果: {}",
    },
    "en": {
        "prompt": "Please enter a regular expression",
        "exit_info": "to exit.",
        "error_message": "The regular expression seems incorrect. Please try again.",
        "test_request": "please test",
        "result_success": "✅ Regular expression is correct:",
        "result_failure": "❌ Regular expression doesn't match",
        "api_error": "API error occurred: ",
        "keyboard_interrupt": "\nExiting.",
        "regex_display": "Regex: {} \nTest strings: {} \nExpected results: {}",
    },
}


class RegexChecker:
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        exit_word: str = "exit",
        language: Literal["ja", "en"] = "ja",
    ):
        """
        Initialize the RegexChecker

        Args:
            model_name: Model name to use
            api_key: OpenAI API key
            exit_word: Word to exit the program
            language: Language to use ("ja" or "en")
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_KEY"))
        self.model_name = model_name or "gpt4o-mini"
        self.exit_word = exit_word
        self.language = language
        self.i18n = I18N[language]

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_regex",
                    "description": "A function that determines whether a regular expression is correct. If the return value is True, the regular expression is determined to be correct, and if False, it is determined to be incorrect.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "regex": {
                                "type": "string",
                                "description": "Regular expression",
                            },
                            "test_strs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "An array of strings to test",
                            },
                            "result_with_test_strs": {
                                "type": "array",
                                "items": {"type": "boolean"},
                                "description": "An array of expected results for the test strings",
                            },
                        },
                        "required": ["regex", "test_strs", "result_with_test_strs"],
                    },
                },
            }
        ]

        self.messages = []
        self.flag = True

    def check_regex(
        self, regex: str, test_strs: List[str], result_with_test_strs: List[bool]
    ) -> bool:
        """
        Check if the regex returns expected results

        Args:
            regex: Regular expression
            test_strs: List of test strings
            result_with_test_strs: List of expected results

        Returns:
            bool: Whether the regex returns expected results
        """
        result = []

        for test_str in test_strs:
            if re.match(regex, test_str):
                result.append(True)
            else:
                result.append(False)
        return result == result_with_test_strs

    def run(self) -> None:
        """
        Run the RegexChecker interactively
        """
        try:
            while True:
                if self.flag:
                    question = input(f"({self.exit_word} {self.i18n['exit_info']})>> ")
                    if question == self.exit_word:
                        break
                    self.messages.append({"role": "user", "content": question})
                else:
                    self.flag = True

                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=self.messages,
                        tools=self.tools,
                        tool_choice="auto",
                    )

                    message = response.choices[0].message

                    if message.tool_calls:
                        tool_call = message.tool_calls[0]

                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.decoder.JSONDecodeError:
                            self.flag = False
                            continue

                        function_response = self.check_regex(
                            regex=arguments["regex"],
                            test_strs=arguments["test_strs"],
                            result_with_test_strs=arguments["result_with_test_strs"],
                        )

                        if function_response:
                            print(self.i18n["result_success"])
                            print(
                                self.i18n["regex_display"].format(
                                    arguments["regex"],
                                    arguments["test_strs"],
                                    arguments["result_with_test_strs"],
                                )
                            )
                            self.flag = True
                        else:
                            print(self.i18n["result_failure"])

                        self.messages.append(
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_call.function.name,
                                            "arguments": tool_call.function.arguments,
                                        },
                                    }
                                ],
                            }
                        )

                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(function_response),
                            }
                        )

                        if not function_response:
                            self.messages.append(
                                {
                                    "role": "user",
                                    "content": self.i18n["error_message"],
                                }
                            )
                            self.flag = False
                    else:
                        self.messages.append(
                            {"role": "assistant", "content": message.content}
                        )
                        self.messages.append(
                            {"role": "user", "content": self.i18n["test_request"]}
                        )
                        self.flag = False

                except APIError as e:
                    print(f"{self.i18n['api_error']}{e}")
                    self.flag = True

        except KeyboardInterrupt:
            print(self.i18n["keyboard_interrupt"])


def main():
    """
    Main function - Parse command line arguments and run RegexChecker
    """
    parser = argparse.ArgumentParser(
        description="Regular Expression Checker using OpenAI"
    )
    parser.add_argument(
        "--model", "-m", type=str, default="gpt-4o-mini", help="OpenAI model to use"
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        choices=["en", "ja"],
        default="en",
        help="Language to use (en or ja)",
    )
    parser.add_argument(
        "--exit-word", "-e", type=str, default="exit", help="Word to exit the program"
    )
    args = parser.parse_args()

    regex_checker = RegexChecker(
        model_name=args.model, exit_word=args.exit_word, language=args.language
    )
    regex_checker.run()


if __name__ == "__main__":
    main()

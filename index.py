import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()


class RegexChecker:
    def __init__(self, model_name=None, api_key=None, exit_word="exit"):
        if api_key is None:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            openai.api_key = api_key
        if model_name is None:
            self.model_name = "gpt-3.5-turbo-0613"
        else:
            self.model_name = model_name
        if exit_word is None:
            self.exit_word = "exit"
        else:
            self.exit_word = exit_word
        self.functions = [
            {
                "name": "check_regex",
                "description": "正規表現が正しいかどうかを判定する関数。戻り値がTrueの場合は正規表現は正しいと判断する、Falseの場合は正しくないと判断する。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regex": {"type": "string", "description": "正規表現"},
                        "test_strs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "テストする文字列の配列",
                        },
                        "result_with_test_strs": {
                            "type": "array",
                            "items": {"type": "boolean"},
                            "description": "テストする文字列に対する推定している結果の配列",
                        },
                    },
                    "required": ["regex", "test_strs", "result_with_test_strs"],
                },
            }
        ]
        self.messages = []
        self.flag = True

    def check_regex(self, regex, test_strs, result_with_test_strs):
        import re

        result = []

        for test_str in test_strs:
            if re.match(regex, test_str):
                result.append(True)
            else:
                result.append(False)
        return result == result_with_test_strs

    def run(self):
        try:
            while True:
                if self.flag:
                    question = input(f"({self.exit_word}で終了)>> ")
                    if question == self.exit_word:
                        break
                    self.messages.append({"role": "user", "content": question})
                else:
                    self.flag = True
                responses = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=self.messages,
                    functions=self.functions,
                    function_call="auto",
                )
                message_tmp = responses["choices"][0]["message"]
                if message_tmp.get("function_call"):
                    try:
                        arguments = json.loads(
                            message_tmp["function_call"]["arguments"]
                        )
                    except json.decoder.JSONDecodeError:
                        pass
                    function_response = self.check_regex(
                        regex=arguments["regex"],
                        test_strs=arguments["test_strs"],
                        result_with_test_strs=arguments["result_with_test_strs"],
                    )
                    if function_response:
                        print(
                            arguments["regex"],
                            arguments["test_strs"],
                            arguments["result_with_test_strs"],
                        )
                        self.flag = True
                        print("正規表現が正しいと判断しました。")
                    self.messages.append(
                        {
                            "role": "function",
                            "name": message_tmp["function_call"]["name"],
                            "content": str(function_response),
                        }
                    )

                    if not function_response:
                        self.messages.append(
                            {"role": "user", "content": "正規表現が間違っているようです。もう一度入力してください。"}
                        )
                        self.flag = False
                else:
                    self.messages.append(
                        {"role": "assistant", "content": message_tmp["content"]}
                    )
                    self.messages.append({"role": "user", "content": "testして"})
                    self.flag = False
        except KeyboardInterrupt:
            pass


regex_checker = RegexChecker()
regex_checker.run()

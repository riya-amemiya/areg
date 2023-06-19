import json
import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

model_name = "gpt-3.5-turbo-0613"

# AIが使うことができる関数を羅列する
functions = [
    # AIが、質問に対してこの関数を使うかどうか、
    # また使う時の引数は何にするかを判断するための情報を与える
    {
        "name": "check_regex",
        "description": "正規表現が正しいかどうかを判定する関数。戻り値がTrueの場合は正規表現は正しいと判断する、Falseの場合は正しくないと判断する。",
        "parameters": {
            "type": "object",
            "properties": {
                # 引数の情報
                "regex": {"type": "string", "description": "正規表現"},
                "test_strs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "テストする文字列の配列",
                },
                # 　求める結果
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


def check_regex(regex, test_strs, result_with_test_strs):
    import re

    result = []

    for test_str in test_strs:
        if re.match(regex, test_str):
            result.append(True)
        else:
            result.append(False)
    return result == result_with_test_strs


messages = []
flag = True
try:
    while True:
        if flag:
            question = input("(exitで終了)>> ")
            if question == "exit":
                break
            messages.append({"role": "user", "content": question})
        else:
            flag = True
        responses = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            functions=functions,
            function_call="auto",
        )
        message_tmp = responses["choices"][0]["message"]
        if message_tmp.get("function_call"):
            try:
                arguments = json.loads(message_tmp["function_call"]["arguments"])
            except json.decoder.JSONDecodeError:
                pass
            function_response = check_regex(
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
                flag = True
                print("正規表現が正しいと判断しました。")
            messages.append(
                {
                    "role": "function",
                    "name": message_tmp["function_call"]["name"],
                    "content": str(function_response),
                }
            )

            if not function_response:
                messages.append(
                    {"role": "user", "content": "正規表現が間違っているようです。もう一度入力してください。"}
                )
                flag = False
        else:
            messages.append({"role": "assistant", "content": message_tmp["content"]})
            messages.append({"role": "user", "content": "testして"})
            flag = False
except KeyboardInterrupt:
    pass

print("=======")
print(arguments["regex"])
print("=======")

import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

model_name = "gpt-3.5-turbo-0613"

question = "pyenvとpipenvの環境構築方法について教えてください。"

response = openai.ChatCompletion.create(
    model=model_name,
    messages=[
        {"role": "user", "content": question},
    ],
    stream=True,
)

for message in response:
    print(message["choices"][0]["delta"].get("content", ""), end="")

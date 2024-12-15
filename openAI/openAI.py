import os
from openai import OpenAI

# Инициализация клиента OpenAI с использованием переменной окружения
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Пример запроса к API
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello world"}]
)

print(response)

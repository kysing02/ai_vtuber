import os
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
# Send a streaming request
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "say one to hundred"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
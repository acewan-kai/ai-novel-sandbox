"""Quick API Test"""
import os
import asyncio
from pathlib import Path

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

api_key = os.environ.get("DEEPSEEK_API_KEY", "")
print(f"API Key length: {len(api_key)}")

async def test_api():
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    try:
        response = await client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=20,
        )
        print(f"[OK] API works!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"[FAIL] API error: {type(e).__name__}: {e}")

asyncio.run(test_api())

import asyncio
import aiohttp
import json
import random
import string

API_URL = "https://api.ankey.io/v1/wordbooks"
CREATE_COUNT = 10000
DELAY = 0.01

EMOJIS = ["🔥", "✨", "🎯", "📚", "🚀", "🧠", "👀", "💡", "🎮"]

with open("api.json", "r", encoding="utf-8") as f:
    API_KEY = json.load(f)["api_keys"][0]


def rand_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def rand_text(min_len, max_len):
    return f"{rand_string(random.randint(min_len, max_len))} {random.choice(EMOJIS)}"


async def create_wordbook(session, index):
    payload = {
        "title": rand_text(16, 16),
        "description": rand_text(199, 200),
        "eyecatch_image": {},
        "tag_names": ["test"],
        "status": "publish",
        "sort_logic": "random",
        "items": [],
        "items_count": 0
    }

    async with session.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload
    ) as resp:
        text = await resp.text()
        if resp.status in (200, 201):
            print(f"✅ [{index}] Wordbook created")
        else:
            print(f"❌ [{index}] Failed {resp.status}: {text}")

    await asyncio.sleep(DELAY)


async def main():
    async with aiohttp.ClientSession() as session:
        for i in range(1, CREATE_COUNT + 1):
            await create_wordbook(session, i)

    print("==== Complete! ====")


asyncio.run(main())

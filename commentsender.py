import asyncio
import aiohttp
import json
import random
import string
from itertools import cycle

WORDBOOK_ID = "TEST"
COMMENT_URL = f"https://api.ankey.io/v1/wordbooks/{WORDBOOK_ID}/comments"

BASE_MESSAGE = "TEST"
USE_RANDOM_STRING = True
USE_RANDOM_EMOJI = True

SEND_COUNT = 3         
CONCURRENCY = 100          
DELAY = 10              

EMOJIS = ["🔥", "✨", "👍", "😄", "💯", "🚀", "👀"]

with open("api.json", "r", encoding="utf-8") as f:
    API_KEYS = json.load(f)["api_keys"]

api_key_cycle = cycle(API_KEYS)
semaphore = asyncio.Semaphore(CONCURRENCY)


def random_string(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def build_message():
    msg = BASE_MESSAGE

    if USE_RANDOM_STRING:
        msg += " " + random_string()

    if USE_RANDOM_EMOJI:
        msg += " " + random.choice(EMOJIS)

    return msg


async def send_comment(session, index):
    api_key = next(api_key_cycle)
    payload = {
        "content": build_message()
    }

    async with semaphore:
        async with session.post(
            COMMENT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload
        ) as resp:
            text = await resp.text()

            if resp.status in (200, 201):
                print(f"✅ [{index}] Comment sent")
            else:
                print(f"❌ [{index}] Failed {resp.status}: {text}")

        await asyncio.sleep(DELAY)


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_comment(session, i + 1)
            for i in range(SEND_COUNT)
        ]
        await asyncio.gather(*tasks)

    print("==== Complete! ====")


asyncio.run(main())

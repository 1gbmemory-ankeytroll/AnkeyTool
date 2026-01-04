import asyncio
import aiohttp
import json
from itertools import cycle
from pathlib import Path

USERS_URL = "https://api.ankey.io/v1/users/search"
FOLLOW_URL_TPL = "https://api.ankey.io/v1/users/{uid}/follow"

BATCH_SIZE = 150
FOLLOW_CONCURRENCY = 100
FOLLOW_DELAY = 0

FOLLOWED_FILE = Path("followed.txt")

with open("api.json", "r", encoding="utf-8") as f:
    API_KEYS = json.load(f)["api_keys"]

api_key_cycle = cycle(API_KEYS)
follow_semaphore = asyncio.Semaphore(FOLLOW_CONCURRENCY)


def load_followed():
    if not FOLLOWED_FILE.exists():
        return set()
    return set(line.strip() for line in FOLLOWED_FILE.open("r", encoding="utf-8"))


def save_followed(uid):
    with FOLLOWED_FILE.open("a", encoding="utf-8") as f:
        f.write(uid + "\n")


def extract_ids(data):
    for key in ("users", "items", "data", "results"):
        if key in data and isinstance(data[key], list):
            return [u["id"] for u in data[key] if isinstance(u, dict) and "id" in u]
    return []


async def follow_user(session, uid, followed_set):
    if uid in followed_set:
        print(f"⏭️ Skip (already followed): {uid}")
        return

    api_key = next(api_key_cycle)
    url = FOLLOW_URL_TPL.format(uid=uid)

    async with follow_semaphore:
        async with session.put(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={}
        ) as resp:
            if resp.status in (200, 204, 409):
                print(f"✅ Followed: {uid}")
                followed_set.add(uid)
                save_followed(uid)
            else:
                text = await resp.text()
                print(f"❌ Follow failed {uid}: {resp.status} {text}")

        await asyncio.sleep(FOLLOW_DELAY)


async def process_batch(session, user_ids, followed_set):
    tasks = [
        follow_user(session, uid, followed_set)
        for uid in user_ids
        if uid not in followed_set
    ]
    if tasks:
        await asyncio.gather(*tasks)


async def main():
    followed_set = load_followed()
    print(f"📂 Existing Followers: {len(followed_set)}")

    cursor = None
    total = 0

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"limit": BATCH_SIZE}
            if cursor:
                params["cursor"] = cursor

            async with session.get(
                USERS_URL,
                headers={"Authorization": f"Bearer {API_KEYS[0]}"},
                params=params
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ users fetch failed: {resp.status} {text}")
                    break

                data = await resp.json()
                user_ids = extract_ids(data)

                if not user_ids:
                    print("No users acquired. Terminated.")
                    break

                print(f"👥 {len(user_ids)} Human Acquisition")
                await process_batch(session, user_ids, followed_set)

                total += len(user_ids)
                print(f"🔢 Cumulative processing count: {total}")

                cursor = data.get("cursor") or data.get("next_cursor")
                if not cursor:
                    print("Next cursor not present. Done.")
                    break


asyncio.run(main())

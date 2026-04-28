import aiohttp
from loguru import logger
from datetime import datetime

from config import API_URL


def format_datetime(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str

async def rewind(number: int):
    try:
        with open("data/rewind.txt", "w") as f:
            f.write(str(number))
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL + "reset") as resp:
                resp.raise_for_status()
            async with session.post(API_URL + "rewind", params={"n": number}) as resp:
                resp.raise_for_status()
                logger.info("Rewind " + str(number))
    except Exception as e:
        logger.error(f"Rewind failed: {e}")

async def fetch_patches():
    try:
        while 1:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL+"latest") as resp:
                    resp.raise_for_status()
                    data : dict = await resp.json()
                    logger.trace(data.get("data", {}).get("entries", []))
                    logger.trace(data)
                    if data.get("is_caught_up"):
                        break
    except Exception as e:
        logger.error(f"Get email list failed: {e}")
        return []

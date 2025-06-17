import asyncio
import aiohttp

from aiogram import Bot
from app.db import *

async def fetch_result(cookie):
    headers = {"Cookie": cookie}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://checkege.rustest.ru/api/exam", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        print(f"fetch_result error: {e}")
        return None

async def process_user(tg_id, cookie, response, bot):
    try:
        current_result = await fetch_result(cookie)
        response = json.loads(response)
        if current_result is not None and current_result != response:
            await bot.send_message(chat_id=tg_id, text="Тебе пришли результаты!")
            await add_to_database(tg_id, cookie, response)
        elif current_result is None:
            await bot.send_message(chat_id=tg_id, text="Что-то сломалось, попробуй перезапустить бота")
            print(f"{tg_id} упал (result None)")
            return
    except Exception as e:
        await bot.send_message(chat_id=tg_id, text="Что-то сломалось, попробуй перезапустить бота")
        print(f"{tg_id} упал")

async def background_loop(bot: Bot):
    while True:
        users = await get_users()
        for tg_id, cookie, response in users:
            asyncio.create_task(process_user(tg_id, cookie, response, bot))
        await asyncio.sleep(30)
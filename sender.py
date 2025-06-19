import asyncio
import aiohttp

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

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

        if current_result is None:
            print(f"{tg_id} упал (result None)")
            return

        if await hash_result(current_result) != response:
            try:
                await bot.send_message(chat_id=tg_id, text="Тебе пришли результаты!")
                await add_to_database(tg_id, cookie, current_result)
                print(f"{tg_id} пришли резы")
            except TelegramForbiddenError:
                print(f"Пользователь {tg_id} заблокировал бота.")
                await remove_user(tg_id)
        else:
            print(f"{tg_id} не пришли резы")

    except Exception as e:
        print(f"{tg_id} упал с ошибкой: {e}")

async def background_loop(bot: Bot):
    while True:
        users = await get_users()
        for tg_id, cookie, response in users:
            asyncio.create_task(process_user(tg_id, cookie, response, bot))
        await asyncio.sleep(30)
import asyncio
from aiogram import Bot, Dispatcher

from app.db import init_db
from config import TOKEN
from app.handlers import router
from sender import background_loop

async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(background_loop(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
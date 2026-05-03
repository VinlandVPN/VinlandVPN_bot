import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers.user import user_router
from bot.handlers.admin import admin_router


async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin_router)
    dp.include_router(user_router)

    print("Aiogram-бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

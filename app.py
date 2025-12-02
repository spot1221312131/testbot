import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv, find_dotenv
from handlers_bot.user_private import user_private_router

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv('TOKEN'), parse_mode=ParseMode.HTML)

dp = Dispatcher()

dp.include_router(user_private_router)

async def main():
    await dp.start_polling(bot)


asyncio.run(main())
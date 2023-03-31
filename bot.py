import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import router
from settings import TOKEN, LOG_FILE


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE,
                        level=logging.INFO,
                        filemode='a',
                        datefmt='%Y-%m-%d, %H:%M',
                        format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')
    log = logging.getLogger('Bot')
    asyncio.run(main())

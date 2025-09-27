import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Токен бота (замени на свой)
BOT_TOKEN = "7843215433:AAFDpF0rb5Yvp0QZQtEdR6JYoHZQ0LhYhqs"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем клавиатуру с кнопкой
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Перейти в приложение",
                    url="https://t.me/suslikpizzabbot/killsussnos"
                )
            ]
        ]
    )
    
    await message.answer(
        "привет! killsus лучший sn#seр акк#у#то#\n"
        "Нажми на кнопку ниже что бы перейти в приложение",
        reply_markup=keyboard
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

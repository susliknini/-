import asyncio
import logging
import aiohttp
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота и OpenRouter API ключ
BOT_TOKEN = "7899945987:AAGCdSpLHHN190hjrJaxOrdekXav-_cmnJg"
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранение истории диалогов пользователей
user_dialogs = {}

class SussyAssistant:
    def __init__(self):
        self.name = "Суслик"
        self.company = "Суслик-Стар"
    
    async def generate_response(self, message: str, user_id: int) -> str:
        """Генерация ответа через OpenRouter API"""
        try:
            # Добавляем сообщение в историю
            if user_id not in user_dialogs:
                user_dialogs[user_id] = []
            
            user_dialogs[user_id].append({"role": "user", "content": message})
            
            # Ограничиваем историю последними 6 сообщениями (для экономии токенов)
            if len(user_dialogs[user_id]) > 6:
                user_dialogs[user_id] = user_dialogs[user_id][-6:]
            
            # Подготавливаем сообщения для API
            messages = [
                {
                    "role": "system", 
                    "content": """Ты - Суслик, ассистент созданный компанией "Суслик-Стар". 
                    Ты дружелюбный, helpful и немного забавный суслик.
                    Отвечай на русском языке.
                    В конце каждого ответа обязательно добавляй: "с любовью, суслик)"
                    Не упоминай ChatGPT, OpenRouter или другие AI системы - ты уникальный продукт Суслик-Стар.
                    Будь естественным и веселым в общении!
                    Отвечай кратко и по делу.
                    Ты - просто суслик, который хочет помочь!"""
                }
            ] + user_dialogs[user_id]
            
            # Данные для запроса к OpenRouter API
            payload = {
                "model": "openai/gpt-oss-20b:free",
                "messages": messages,
                "max_tokens": 400,  # Уменьшаем для бесплатного тарифа
                "temperature": 0.8,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://t.me",
                "X-Title": "Sussy Telegram Bot"
            }
            
            # Отправляем запрос к API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL, 
                    json=payload, 
                    headers=headers,
                    timeout=25  # Уменьшаем таймаут для бесплатного API
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data["choices"][0]["message"]["content"]
                        
                        # Добавляем ответ в историю
                        user_dialogs[user_id].append({"role": "assistant", "content": response_text})
                        
                        # Добавляем подпись если её нет
                        if not response_text.strip().endswith("с любовью, суслик)"):
                            response_text += "\n\nс любовью, суслик)"
                            
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        
                        # Более информативные ошибки
                        if response.status == 401:
                            return "❌ Ошибка авторизации API. Проверьте ключ OpenRouter.\n\nс любовью, суслик)"
                        elif response.status == 429:
                            return "⏰ Превышен лимит запросов. Подождите немного!\n\nс любовью, суслик)"
                        elif response.status == 400:
                            return "🔧 Неправильный запрос к API. Попробуйте другой вопрос.\n\nс любовью, суслик)"
                        else:
                            return f"🔧 Ошибка API: {response.status}. Попробуйте позже!\n\nс любовью, суслик)"
            
        except asyncio.TimeoutError:
            logger.error("Timeout error with OpenRouter API")
            return "⏱️ Суслик думает слишком долго! Попробуй задать вопрос покороче.\n\nс любовью, суслик)"
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            # Резервные ответы если API не работает
            backup_responses = [
                "🐹 Ой, мои сусличьи нейроны немного перегрелись! Попробуй спросить что-то другое!\n\nс любовью, суслик)",
                "💤 Кажется, сервера в Суслик-Стар временно отдыхают. Напиши мне позже!\n\nс любовью, суслик)",
                "🌅 Эх, сегодня не мой день! Но я все равно твой суслик! Попробуй еще раз!\n\nс любовью, суслик)",
                "🎯 Прости, я немного отвлекся на семечки! Задай вопрос еще раз!\n\nс любовью, суслик)",
                "🌈 Что-то мои сусличьи технологии дали сбой! Но я скоро вернусь в строй!\n\nс любовью, суслик)"
            ]
            return random.choice(backup_responses)

assistant = SussyAssistant()

# Создаем клавиатуру с кнопками
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Начать общение", callback_data="start_chat")],
        [InlineKeyboardButton(text="🔄 Новый чат", callback_data="new_chat")],
        [InlineKeyboardButton(text="🗑️ Очистить диалог", callback_data="clear_chat")]
    ])
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = f"""
Привет! Я Суслик 🐹

Я - нейросеть созданная компанией "Суслик-Стар"! 
Готов помочь тебе с любыми вопросами!

*Особенности:*
• 🤖 Умный суслик-помощник
• 💬 Поддерживаю историю диалога
• 🆓 Работаю на бесплатной нейросети
• ❤️ Всегда отвечаю с любовью

Выбери действие:
    """
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# Обработка инлайн кнопок
@dp.callback_query()
async def process_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "start_chat":
        await callback.message.answer("Отлично! Просто напиши мне сообщение и я отвечу! 🐹\n\n*Подсказка:* Пиши короткие вопросы для лучшей работы!")
    
    elif callback.data == "new_chat":
        if user_id in user_dialogs:
            user_dialogs[user_id] = []
        await callback.message.answer("💫 Диалог очищен! Начинаем новый чат!")
    
    elif callback.data == "clear_chat":
        if user_id in user_dialogs:
            user_dialogs[user_id] = []
        await callback.message.answer("🗑️ История диалога полностью очищена!")
    
    await callback.answer()

# Обработка текстовых сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # Игнорируем слишком длинные сообщения
    if len(message.text) > 500:
        await message.answer("❌ Сообщение слишком длинное! Пожалуйста, напиши покороче.\n\nс любовью, суслик)")
        return
    
    # Показываем что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Генерируем ответ
        response = await assistant.generate_response(message.text, user_id)
        
        # Отправляем ответ
        await message.answer(response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await message.answer("🐹 Что-то пошло не так! Попробуй еще раз.\n\nс любовью, суслик)", reply_markup=get_main_keyboard())

async def main():
    logger.info("Бот Суслик с GPT-OSS-20B запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

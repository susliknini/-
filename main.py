import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import g4f

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "7899945987:AAGCdSpLHHN190hjrJaxOrdekXav-_cmnJg"

# Инициализация б и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранение истории диалогов пользователей
user_dialogs = {}

class SussyAssistant:
    def __init__(self):
        self.name = "Суслик"
        self.company = "Суслик-Стар"
    
    async def generate_response(self, message: str, user_id: int) -> str:
        """Генерация ответа через g4f"""
        try:
            # Добавляем сообщение в историю
            if user_id not in user_dialogs:
                user_dialogs[user_id] = []
            
            user_dialogs[user_id].append({"role": "user", "content": message})
            
            # Ограничиваем историю последними 10 сообщениями
            if len(user_dialogs[user_id]) > 10:
                user_dialogs[user_id] = user_dialogs[user_id][-10:]
            
            # Создаем промпт с контекстом
            messages = [
                {"role": "system", "content": f"""Ты - Суслик, ассистент созданный компанией "Суслик-Стар". 
                Ты дружелюбный, суслик и немного забавный. 
                Отвечай на русском языке.
                В конце каждого ответа обязательно добавляй: "с любовью, суслик)" 
                Не упоминай ChatGPT или другие AI системы - ты уникальный продукт Суслик-Стар."""}
            ] + user_dialogs[user_id]
            
            # Пробуем разные работающие провайдеры
            providers = [
                g4f.Provider.FreeGpt,
                g4f.Provider.GptGo,
                g4f.Provider.You,
                g4f.Provider.Liaobots,
                g4f.Provider.ChatBase
            ]
            
            response = None
            last_error = None
            
            for provider in providers:
                try:
                    logger.info(f"Пробуем провайдер: {provider.__name__}")
                    response = await asyncio.to_thread(
                        g4f.ChatCompletion.create,
                        model=g4f.models.gpt_4,
                        messages=messages,
                        provider=provider,
                        timeout=60
                    )
                    if response:
                        break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Провайдер {provider.__name__} не сработал: {e}")
                    continue
            
            if not response:
                raise Exception(f"Все провайдеры не сработали. Последняя ошибка: {last_error}")
            
            # Добавляем ответ в историю
            user_dialogs[user_id].append({"role": "assistant", "content": response})
            
            # Добавляем подпись если её нет
            if not response.strip().endswith("с любовью, суслик)"):
                response += "\n\nс любовью, суслик)"
                
            return response
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return f"Ой, что-то пошло не так! Попробуйте позже.\n\nс любовью, суслик)"

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

Я головка от нейросети созданная компанией "Суслик-Стар"! 
Готов тебе помогать пон да

Выбери действие что бы начать аш диалог:
    """
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# Обработка инлайн кнопок
@dp.callback_query()
async def process_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "start_chat":
        await callback.message.answer("Отлично! я гордый суслик пиши текст ну оч хочеш")
    
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
    
    # Показываем что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Генерируем ответ
    response = await assistant.generate_response(message.text, user_id)
    
    # Отправляем ответ
    await message.answer(response, reply_markup=get_main_keyboard())

async def main():
    logger.info("Бот Суслик запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

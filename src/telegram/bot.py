from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from typing import Optional

_bot: Optional[Bot] = None
_dp: Optional[Dispatcher] = None


def init_bot(token: str) -> Bot:
    global _bot, _dp
    _bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    _dp = Dispatcher()
    return _bot


def get_bot() -> Optional[Bot]:
    return _bot


def get_dp() -> Optional[Dispatcher]:
    return _dp

import logging
from aiogram import Router, types
from src.database import get_all_settings, set_setting
from src.telegram.keyboards import intervals_kb
from src.scheduler.manager import reschedule_jobs

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "menu_intervals")
async def menu_intervals(callback: types.CallbackQuery):
    current = await get_all_settings()
    text = "⏱️ <b>Интервалы проверок</b>\n\nВыберите интервал для каждого типа проверки:"
    await callback.message.edit_text(text, reply_markup=intervals_kb(current))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_interval:"))
async def set_interval(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некорректные данные")
        return

    check_type, value = parts[1], parts[2]
    key_map = {
        "nodes": "nodes_interval_seconds",
        "metrics": "metrics_interval_seconds",
        "traffic": "traffic_interval_seconds",
        "inbounds": "inbounds_interval_seconds",
    }
    key = key_map.get(check_type)
    if not key:
        await callback.answer("Неизвестный тип")
        return

    await set_setting(key, value)
    await reschedule_jobs()
    await callback.answer(f"Интервал {check_type} изменён на {value}с")

    current = await get_all_settings()
    await callback.message.edit_reply_markup(reply_markup=intervals_kb(current))

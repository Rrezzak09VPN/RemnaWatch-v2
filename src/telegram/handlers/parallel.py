import logging
from aiogram import Router, types
from src.database import get_setting, set_setting
from src.telegram.keyboards import parallel_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "menu_parallel")
async def menu_parallel(callback: types.CallbackQuery):
    current = await get_setting("singbox_parallel_count")
    text = (
        "🔢 <b>Параллелизм sing-box</b>\n\n"
        f"Текущее значение: <b>{current}</b>\n\n"
        "Количество одновременных проверок inbound'ов.\n"
        "Чем выше значение — тем быстрее, но больше нагрузка на CPU."
    )
    await callback.message.edit_text(text, reply_markup=parallel_kb(current))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_parallel:"))
async def set_parallel(callback: types.CallbackQuery):
    value = callback.data.split(":")[1]
    await set_setting("singbox_parallel_count", value)
    await callback.answer(f"Параллелизм изменён на {value}")
    await menu_parallel(callback)

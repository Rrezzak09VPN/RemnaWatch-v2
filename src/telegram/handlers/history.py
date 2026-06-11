import logging
from aiogram import Router, types
from src.database import get_recent_alerts
from src.telegram.keyboards import back_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "alerts_history")
async def show_history(callback: types.CallbackQuery):
    alerts = await get_recent_alerts(20)
    if not alerts:
        text = "📜 <b>История алертов</b>\n\nПока нет алертов."
    else:
        text = "📜 <b>История алертов (последние 20)</b>\n\n"
        for alert in alerts:
            ts = alert.get("timestamp", "")[:19] if alert.get("timestamp") else ""
            msg = alert.get("message", "")
            resolved = "✅" if alert.get("resolved") else "🔴"
            text += f"{resolved} [{ts}] {msg[:100]}\n\n"

    await callback.message.edit_text(text, reply_markup=back_kb())
    await callback.answer()

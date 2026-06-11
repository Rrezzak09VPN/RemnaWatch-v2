import logging

from aiogram import Router, types

from src.database import get_all_inbounds, get_all_nodes
from src.telegram.keyboards import back_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "status")
async def show_status(callback: types.CallbackQuery):
    nodes = await get_all_nodes()
    inbounds = await get_all_inbounds()

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

    text = (
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

    await callback.message.edit_text(text, reply_markup=back_kb())
    await callback.answer()

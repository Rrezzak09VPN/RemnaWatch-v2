import logging

from aiogram import Router, types

from src.checks.traffic_checker import bytes_human
from src.database import get_enabled_nodes
from src.telegram.keyboards import back_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "traffic")
async def show_traffic(callback: types.CallbackQuery):
    nodes = await get_enabled_nodes()
    text = "🚦 <b>Трафик нод</b>\n\n"
    if not nodes:
        text += "Нет включённых нод."
    for node in nodes:
        used = int(node.get("traffic_used_bytes") or 0)
        limit = int(node.get("traffic_limit_bytes") or 0)
        if limit > 0:
            pct = used / limit * 100
            limit_text = f"{bytes_human(used)} / {bytes_human(limit)} ({pct:.1f}%)"
        else:
            limit_text = f"{bytes_human(used)} / ∞"
        text += f"<b>{node['name']}</b>\n  {limit_text}\n\n"
    await callback.message.edit_text(text, reply_markup=back_kb())
    await callback.answer()

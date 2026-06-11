import logging
from aiogram import Router, types
from src.database import get_all_inbounds, toggle_inbound_enabled
from src.telegram.keyboards import inbounds_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "menu_inbounds")
async def menu_inbounds(callback: types.CallbackQuery):
    inbounds = await get_all_inbounds()
    text = "🌐 <b>Inbound'ы</b>\n\nНажмите на inbound, чтобы включить/выключить мониторинг:\n\n"
    for ib in inbounds:
        status = ib.get("last_status", "UNKNOWN")
        enabled = "✅" if ib.get("enabled") else "❌"
        ignored = " (игнор)" if ib.get("ignored") else ""
        archived = " (архив)" if ib.get("archived") else ""
        proto = f"{ib.get('protocol') or '?'}/{ib.get('network') or '?'}"
        disabled = " (disabled в панели)" if ib.get("is_disabled") else ""
        text += f"{enabled} <b>{ib.get('remark', ib['uuid'][:8])}</b> — {status} [{proto}]{disabled}{ignored}{archived}\n"

    await callback.message.edit_text(text, reply_markup=inbounds_kb(inbounds))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("toggle_inbound:"))
async def toggle_inbound(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]
    new_state = await toggle_inbound_enabled(uuid)
    status = "включен" if new_state else "выключен"
    await callback.answer(f"Inbound {status}")
    await menu_inbounds(callback)

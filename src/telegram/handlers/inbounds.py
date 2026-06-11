import logging
from aiogram import F, Router, types
from src.database import (
    get_all_inbounds,
    get_enabled_inbound_uuids,
    get_inbound_by_uuid,
    toggle_inbound_enabled,
)
from src.telegram.keyboards import UNSUPPORTED_PROTOCOLS, inbounds_kb, is_inbound_supported

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "menu_inbounds")
async def menu_inbounds(callback: types.CallbackQuery):
    inbounds = await get_all_inbounds()
    enabled_uuids = await get_enabled_inbound_uuids()
    text = "🌐 <b>Inbound'ы</b>\n\nНажмите на inbound, чтобы включить/выключить мониторинг:\n\n"
    for ib in inbounds:
        status = ib.get("last_status", "UNKNOWN")
        enabled = "✅" if ib.get("enabled") else "❌"
        ignored = " (игнор)" if ib.get("ignored") else ""
        archived = " (архив)" if ib.get("archived") else ""
        proto = f"{ib.get('protocol') or '?'}/{ib.get('network') or '?'}"
        disabled = " (disabled в панели)" if ib.get("is_disabled") else ""
        unsupported = "" if is_inbound_supported(ib) else " 🚫 не поддерживается"
        text += f"{enabled} <b>{ib.get('remark') or ib['uuid'][:8]}</b> — {status} [{proto}]{unsupported}{disabled}{ignored}{archived}\n"

    await callback.message.edit_text(text, reply_markup=inbounds_kb(inbounds, enabled_uuids).as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_inbound:"))
async def toggle_inbound(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]

    ib = await get_inbound_by_uuid(uuid)
    if not ib:
        await callback.answer("❌ Inbound не найден", show_alert=True)
        return

    # Серверная валидация: защищает и от старых клавиатур, и от других точек входа.
    protocol = (ib.get("protocol") or "").lower()
    network = (ib.get("network") or "").lower()
    if protocol in UNSUPPORTED_PROTOCOLS or network in UNSUPPORTED_PROTOCOLS:
        await callback.answer(
            f"⚠️ Протокол {network or protocol} не поддерживается sing-box и не может мониториться",
            show_alert=True,
        )
        return

    new_state = await toggle_inbound_enabled(uuid)
    status = "включен" if new_state else "выключен"
    await callback.answer(f"Inbound {status}")
    await menu_inbounds(callback)


@router.callback_query(F.data.startswith("noop:"))
async def noop_inbound(callback: types.CallbackQuery):
    await callback.answer(
        "🚫 Этот протокол не поддерживается sing-box — мониторинг недоступен",
        show_alert=False,
    )

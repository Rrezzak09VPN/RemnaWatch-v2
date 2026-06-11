import logging
from aiogram import Router, types
from src.database import get_all_nodes, toggle_node_enabled
from src.telegram.keyboards import nodes_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "menu_nodes")
async def menu_nodes(callback: types.CallbackQuery):
    nodes = await get_all_nodes()
    text = "🖥️ <b>Ноды</b>\n\nНажмите на ноду, чтобы включить/выключить мониторинг:\n\n"
    for node in nodes:
        status = node.get("last_status", "UNKNOWN")
        enabled = "✅" if node.get("enabled") else "❌"
        ignored = " (игнор)" if node.get("ignored") else ""
        archived = " (архив)" if node.get("archived") else ""
        text += f"{enabled} <b>{node['name']}</b> — {status}{ignored}{archived}\n"

    await callback.message.edit_text(text, reply_markup=nodes_kb(nodes))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("toggle_node:"))
async def toggle_node(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]
    new_state = await toggle_node_enabled(uuid)
    status = "включен" if new_state else "выключен"
    await callback.answer(f"Нода {status}")
    await menu_nodes(callback)

import logging
from aiogram import Router, types
from src.telegram.keyboards import main_menu_kb, back_kb
from src.database import (
    toggle_node_enabled,
    toggle_inbound_enabled,
    ignore_object,
    get_new_objects,
    get_all_inbounds,
    get_all_nodes,
    get_setting,
)
from src.scheduler.manager import trigger_all_checks

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>RemnaWatch</b> — Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "noop")
async def noop(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(lambda c: c.data == "new_objects")
async def show_new_objects(callback: types.CallbackQuery):
    objects = await get_new_objects()
    if not objects:
        await callback.message.edit_text(
            "✅ Все объекты настроены. Новых нет.",
            reply_markup=back_kb(),
        )
        await callback.answer()
        return

    from src.telegram.keyboards import new_objects_kb
    text = "🆕 <b>Новые объекты</b>\n\n"
    for obj in objects:
        text += f"• {obj.get('name', obj['uuid'][:8])} ({obj['obj_type']})\n"
    text += "\nНажмите, чтобы включить:"

    await callback.message.edit_text(text, reply_markup=new_objects_kb(objects))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("ignore_node:"))
async def ignore_node(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]
    await ignore_object("node", uuid)
    await callback.answer("Нода проигнорирована")
    await show_new_objects(callback)


@router.callback_query(lambda c: c.data and c.data.startswith("ignore_inbound:"))
async def ignore_inbound_cb(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]
    await ignore_object("inbound", uuid)
    await callback.answer("Inbound проигнорирован")
    await show_new_objects(callback)


@router.callback_query(lambda c: c.data == "check_now")
async def check_now(callback: types.CallbackQuery):
    await callback.message.edit_text("🔄 Запуск всех проверок...", reply_markup=back_kb())
    await callback.answer()
    await trigger_all_checks()
    await callback.message.edit_text("✅ Проверки завершены. Откройте статус/метрики/трафик для результата.", reply_markup=back_kb())

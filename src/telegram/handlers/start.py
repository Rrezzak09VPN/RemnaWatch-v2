import logging
from aiogram import Router, types
from aiogram.filters import Command
from src.database import get_all_nodes, get_all_inbounds, get_new_objects
from src.telegram.keyboards import main_menu_kb, object_action_kb, new_objects_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    nodes = await get_all_nodes()
    inbounds = await get_all_inbounds()
    new_objs = await get_new_objects()

    text = (
        "🎉 <b>RemnaWatch</b> — мониторинг Remnawave\n\n"
        f"Обнаружено:\n"
        f"• {len(nodes)} нод\n"
        f"• {len(inbounds)} inbound'ов\n\n"
    )

    if new_objs:
        text += f"🆕 <b>{len(new_objs)} объектов ожидают подтверждения</b>\nНажмите /setup для настройки.\n\n"

    text += "Выберите действие:"
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("setup"))
async def cmd_setup(message: types.Message):
    new_objs = await get_new_objects()
    if not new_objs:
        await message.answer("✅ Все объекты уже настроены. Новых объектов нет.")
        return

    text = "🆕 <b>Объекты, ожидающие подтверждения:</b>\n\n"
    for obj in new_objs:
        name = obj.get("name", obj["uuid"][:8])
        text += f"• {name} ({obj['obj_type']})\n"
    text += "\nНажмите на объект, чтобы включить или игнорировать:"

    await message.answer(text, reply_markup=new_objects_kb(new_objs))

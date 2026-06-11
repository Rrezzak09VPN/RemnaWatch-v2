import logging
from aiogram import Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.database import get_all_nodes, get_thresholds, set_threshold
from src.telegram.keyboards import thresholds_kb, threshold_detail_kb, back_kb

logger = logging.getLogger(__name__)
router = Router()


class ThresholdState(StatesGroup):
    waiting_mem = State()
    waiting_load = State()


@router.callback_query(lambda c: c.data == "menu_thresholds")
async def menu_thresholds(callback: types.CallbackQuery):
    nodes = await get_all_nodes()
    text = "⚙️ <b>Пороги</b>\n\nВыберите ноду для настройки порогов:"
    await callback.message.edit_text(text, reply_markup=thresholds_kb(nodes))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("thresholds_node:"))
async def thresholds_node(callback: types.CallbackQuery):
    uuid = callback.data.split(":")[1]
    thresholds = await get_thresholds(uuid)
    nodes = await get_all_nodes()
    node_name = next((n["name"] for n in nodes if n["uuid"] == uuid), uuid[:8])

    text = (
        f"⚙️ <b>Пороги для {node_name}</b>\n\n"
        f"📊 RAM threshold: {thresholds['memory_percent']}%\n"
        f"📊 Load per core: {thresholds['load_per_core']}\n\n"
        f"Нажмите на параметр для изменения:"
    )
    await callback.message.edit_text(text, reply_markup=threshold_detail_kb(uuid))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_threshold_mem:"))
async def set_threshold_mem(callback: types.CallbackQuery, state: FSMContext):
    uuid = callback.data.split(":")[1]
    await state.set_data({"node_uuid": uuid, "key": "memory_percent"})
    await state.set_state(ThresholdState.waiting_mem)
    await callback.message.edit_text("Введите новое значение RAM threshold (0-100):")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_threshold_load:"))
async def set_threshold_load(callback: types.CallbackQuery, state: FSMContext):
    uuid = callback.data.split(":")[1]
    await state.set_data({"node_uuid": uuid, "key": "load_per_core"})
    await state.set_state(ThresholdState.waiting_load)
    await callback.message.edit_text("Введите новое значение Load per core (например 1.5):")
    await callback.answer()


@router.message(StateFilter(ThresholdState.waiting_mem))
async def handle_mem_input(message: types.Message, state: FSMContext):
    try:
        value = int(message.text.strip())
        if value < 0 or value > 100:
            await message.answer("❌ Значение должно быть от 0 до 100")
            return
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите целое число.")
        return

    data = await state.get_data()
    await set_threshold(data["node_uuid"], "memory_percent", value)
    await state.clear()
    await message.answer(f"✅ Порог RAM изменён на {value}%", reply_markup=back_kb())


@router.message(StateFilter(ThresholdState.waiting_load))
async def handle_load_input(message: types.Message, state: FSMContext):
    try:
        value = float(message.text.strip())
        if value < 0:
            await message.answer("❌ Значение должно быть положительным числом")
            return
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число.")
        return

    data = await state.get_data()
    await set_threshold(data["node_uuid"], "load_per_core", value)
    await state.clear()
    await message.answer(f"✅ Порог Load per core изменён на {value}", reply_markup=back_kb())

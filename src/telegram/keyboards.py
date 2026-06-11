from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Общий статус", callback_data="status")
    builder.button(text="🖥️ Ноды", callback_data="menu_nodes")
    builder.button(text="🌐 Inbound'ы", callback_data="menu_inbounds")
    builder.button(text="📈 Метрики нод", callback_data="metrics")
    builder.button(text="🚦 Трафик нод", callback_data="traffic")
    builder.button(text="⏱️ Интервалы", callback_data="menu_intervals")
    builder.button(text="⚙️ Пороги", callback_data="menu_thresholds")
    builder.button(text="🔢 Параллелизм", callback_data="menu_parallel")
    builder.button(text="🆕 Новые объекты", callback_data="new_objects")
    builder.button(text="📜 История алертов", callback_data="alerts_history")
    builder.button(text="🔄 Проверить сейчас", callback_data="check_now")
    builder.adjust(2)
    return builder.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="main_menu")
    return builder.as_markup()


def nodes_kb(nodes: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for node in nodes:
        status_emoji = "✅" if node.get("enabled") else "❌"
        name = node.get("name", node["uuid"][:8])
        builder.button(
            text=f"{status_emoji} {name}",
            callback_data=f"toggle_node:{node['uuid']}",
        )
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def inbounds_kb(inbounds: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ib in inbounds:
        status_emoji = "✅" if ib.get("enabled") else "❌"
        name = ib.get("remark", ib["uuid"][:8])
        builder.button(
            text=f"{status_emoji} {name}",
            callback_data=f"toggle_inbound:{ib['uuid']}",
        )
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def intervals_kb(current: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nodes_opts = ["30", "60", "120", "300"]
    metrics_opts = ["30", "60", "120", "300"]
    traffic_opts = ["60", "120", "300", "600"]
    inbounds_opts = ["60", "120", "300", "600", "1800"]

    cur_nodes = current.get("nodes_interval_seconds", "60")
    cur_metrics = current.get("metrics_interval_seconds", "60")
    cur_traffic = current.get("traffic_interval_seconds", "120")
    cur_inbounds = current.get("inbounds_interval_seconds", "300")

    builder.row(
        InlineKeyboardButton(text=f"🖥️ Ноды: {cur_nodes}с", callback_data="noop"),
    )
    for opt in nodes_opts:
        marker = "●" if opt == cur_nodes else "○"
        builder.button(text=f"{marker} {opt}с", callback_data=f"set_interval:nodes:{opt}")
    builder.adjust(4)

    builder.row(
        InlineKeyboardButton(text=f"📈 Метрики: {cur_metrics}с", callback_data="noop"),
    )
    for opt in metrics_opts:
        marker = "●" if opt == cur_metrics else "○"
        builder.button(text=f"{marker} {opt}с", callback_data=f"set_interval:metrics:{opt}")
    builder.adjust(4)

    builder.row(
        InlineKeyboardButton(text=f"🚦 Трафик: {cur_traffic}с", callback_data="noop"),
    )
    for opt in traffic_opts:
        marker = "●" if opt == cur_traffic else "○"
        builder.button(text=f"{marker} {opt}с", callback_data=f"set_interval:traffic:{opt}")
    builder.adjust(4)

    builder.row(
        InlineKeyboardButton(text=f"🌐 Inbound'ы: {cur_inbounds}с", callback_data="noop"),
    )
    for opt in inbounds_opts:
        marker = "●" if opt == cur_inbounds else "○"
        builder.button(text=f"{marker} {opt}с", callback_data=f"set_interval:inbounds:{opt}")
    builder.adjust(5)

    builder.button(text="◀️ Назад", callback_data="main_menu")
    return builder.as_markup()


def parallel_kb(current: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for val in ["1", "2", "3", "5"]:
        marker = "●" if val == current else "○"
        builder.button(text=f"{marker} {val}", callback_data=f"set_parallel:{val}")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(4)
    return builder.as_markup()


def object_action_kb(obj_type: str, uuid: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Включить", callback_data=f"toggle_{obj_type}:{uuid}")
    builder.button(text="❌ Игнорировать", callback_data=f"ignore_{obj_type}:{uuid}")
    return builder.as_markup()


def new_objects_kb(objects: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for obj in objects:
        name = obj.get("name", obj["uuid"][:8])
        otype = obj["obj_type"]
        builder.row(
            InlineKeyboardButton(
                text=f"🆕 {name} ({otype})",
                callback_data=f"toggle_{otype}:{obj['uuid']}",
            )
        )
    builder.button(text="◀️ Назад", callback_data="main_menu")
    return builder.as_markup()


def thresholds_kb(nodes: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for node in nodes:
        name = node.get("name", node["uuid"][:8])
        builder.button(text=f"⚙️ {name}", callback_data=f"thresholds_node:{node['uuid']}")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def threshold_detail_kb(node_uuid: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 RAM threshold", callback_data=f"set_threshold_mem:{node_uuid}")
    builder.button(text="📊 Load/core", callback_data=f"set_threshold_load:{node_uuid}")
    builder.button(text="◀️ Назад", callback_data="menu_thresholds")
    builder.adjust(1)
    return builder.as_markup()

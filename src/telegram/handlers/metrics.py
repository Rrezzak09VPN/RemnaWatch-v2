import logging

from aiogram import Router, types

from src.checks.metrics_checker import bytes_to_mib, fetch_node_metrics
from src.config import settings
from src.database import get_enabled_nodes
from src.telegram.keyboards import back_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "metrics")
async def show_metrics(callback: types.CallbackQuery):
    from src.api.remnawave_api import RemnawaveAPI

    api = RemnawaveAPI(settings.remna_api_url, settings.remna_api_token)
    try:
        nodes = await api.get_nodes()
        node_map = {n["uuid"]: n for n in nodes if n.get("uuid")}
        enabled = await get_enabled_nodes()
        text = "📈 <b>Метрики нод</b>\n\n"
        if not enabled:
            text += "Нет включённых нод."
        for db_node in enabled:
            uuid = db_node["uuid"]
            base = node_map.get(uuid)
            if not base:
                text += f"<b>{db_node['name']}</b> ❓ не найдена в API\n\n"
                continue
            metrics = await fetch_node_metrics(api, uuid, base)
            connected = "✅" if base.get("isConnected") else "❌"
            if not metrics:
                text += f"<b>{db_node['name']}</b> {connected}\n  Метрики недоступны в API\n\n"
                continue
            mem_pct = metrics["memoryUsed"] / metrics["memoryTotal"] * 100
            load = metrics["loadAvg"]
            text += (
                f"<b>{metrics['name']}</b> {connected}\n"
                f"  CPU: {metrics['cpus']} ядер\n"
                f"  RAM: {mem_pct:.1f}% ({bytes_to_mib(metrics['memoryUsed']):.0f}/{bytes_to_mib(metrics['memoryTotal']):.0f} MiB)\n"
                f"  Load: {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}\n\n"
            )
    finally:
        await api.close()

    await callback.message.edit_text(text, reply_markup=back_kb())
    await callback.answer()

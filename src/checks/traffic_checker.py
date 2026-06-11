import logging

from src.api.remnawave_api import RemnawaveAPI
from src.database import get_enabled_nodes, get_setting, update_node_traffic

logger = logging.getLogger(__name__)


def bytes_human(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    size = float(value or 0)
    for unit in units:
        if abs(size) < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


async def check_traffic(api: RemnawaveAPI, alert_engine):
    nodes = await api.get_nodes()
    node_map = {n["uuid"]: n for n in nodes if n.get("uuid")}
    enabled_nodes = await get_enabled_nodes()
    warn_percent = float(await get_setting("traffic_warn_percent") or 90)

    for db_node in enabled_nodes:
        uuid = db_node["uuid"]
        node = node_map.get(uuid)
        if not node:
            continue
        await update_node_traffic(uuid, node)

        used = int(node.get("trafficUsedBytes") or 0)
        limit = int(node.get("trafficLimitBytes") or 0)
        tracking = bool(node.get("isTrafficTrackingActive"))

        logger.info(
            "Traffic %s: used=%s limit=%s tracking=%s",
            node.get("name", uuid[:8]), bytes_human(used), bytes_human(limit), tracking,
        )

        if limit <= 0:
            await alert_engine.process("traffic", uuid, "high_traffic", False)
            await alert_engine.process("traffic", uuid, "traffic_limit", False)
            continue

        pct = used / limit * 100 if limit else 0
        await alert_engine.process(
            "traffic", uuid, "high_traffic", pct >= warn_percent,
            f"Traffic: {pct:.1f}% ({bytes_human(used)} / {bytes_human(limit)})",
        )
        await alert_engine.process(
            "traffic", uuid, "traffic_limit", used >= limit,
            f"Traffic limit reached: {bytes_human(used)} / {bytes_human(limit)}",
        )

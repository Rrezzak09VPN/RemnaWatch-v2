import logging

from src.api.remnawave_api import RemnawaveAPI
from src.database import get_enabled_nodes, update_node_status

logger = logging.getLogger(__name__)


async def check_nodes(api: RemnawaveAPI, alert_engine):
    nodes = await api.get_nodes()
    node_map = {n["uuid"]: n for n in nodes if n.get("uuid")}
    enabled_nodes = await get_enabled_nodes()

    for db_node in enabled_nodes:
        uuid = db_node["uuid"]
        api_node = node_map.get(uuid)
        name = db_node.get("name") or uuid[:8]

        if api_node is None:
            status = "UNKNOWN"
            await alert_engine.process("node", uuid, "disabled", False)
            await alert_engine.process("node", uuid, "down", True, "Node disappeared from /api/nodes")
        elif api_node.get("isDisabled"):
            status = "DISABLED"
            await alert_engine.process("node", uuid, "down", False)
            await alert_engine.process("node", uuid, "disabled", True, "Node disabled in Remnawave panel")
        elif not api_node.get("isConnected"):
            status = "DOWN"
            msg = api_node.get("lastStatusMessage") or "Node is not connected to Remnawave"
            await alert_engine.process("node", uuid, "disabled", False)
            await alert_engine.process("node", uuid, "down", True, msg)
        else:
            status = "UP"
            await alert_engine.process("node", uuid, "disabled", False)
            await alert_engine.process("node", uuid, "down", False)

        await update_node_status(uuid, status)
        logger.info("Node %s: %s", name, status)

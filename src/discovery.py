import logging

from src.api.remnawave_api import RemnawaveAPI
from src.database import archive_object, get_uuids_set, upsert_host, upsert_node

logger = logging.getLogger(__name__)


def _extract_host_inbound_uuid(host: dict) -> str:
    raw = host.get("inbound")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("configProfileInboundUuid") or raw.get("uuid") or raw.get("inboundUuid") or ""
    return host.get("config_inbound_uuid") or host.get("configProfileInboundUuid") or ""


async def run_discovery(api: RemnawaveAPI):
    logger.info("Running discovery...")

    nodes = await api.get_nodes()
    hosts = await api.get_hosts()
    inbound_map = await api.get_all_config_inbounds_map()

    api_node_uuids = {n["uuid"] for n in nodes if n.get("uuid")}
    api_host_uuids = {h["uuid"] for h in hosts if h.get("uuid")}

    db_node_uuids = await get_uuids_set("nodes")
    db_host_uuids = await get_uuids_set("inbounds")

    for node in nodes:
        if node.get("uuid"):
            await upsert_node(node)

    for host in hosts:
        if not host.get("uuid"):
            continue
        inbound_uuid = _extract_host_inbound_uuid(host)
        config_ib = inbound_map.get(inbound_uuid.lower()) if inbound_uuid else None
        if not config_ib:
            logger.warning(
                "Host %s: config inbound uuid=%s not found among %s inbounds",
                host.get("remark") or host["uuid"][:8], inbound_uuid or "<empty>", len(inbound_map),
            )
        await upsert_host(host, config_ib, inbound_uuid)

    new_nodes = api_node_uuids - db_node_uuids
    new_hosts = api_host_uuids - db_host_uuids
    missing_nodes = db_node_uuids - api_node_uuids
    missing_hosts = db_host_uuids - api_host_uuids

    for uuid in missing_nodes:
        await archive_object("nodes", uuid)
        logger.info("Node %s archived - disappeared from API", uuid)

    for uuid in missing_hosts:
        await archive_object("inbounds", uuid)
        logger.info("Host %s archived - disappeared from API", uuid)

    logger.info("Discovery complete: %s nodes, %s hosts", len(nodes), len(hosts))
    logger.info("  New nodes: %s, New hosts: %s", len(new_nodes), len(new_hosts))
    logger.info("  Archived nodes: %s, Archived hosts: %s", len(missing_nodes), len(missing_hosts))

    return new_nodes, new_hosts, missing_nodes, missing_hosts

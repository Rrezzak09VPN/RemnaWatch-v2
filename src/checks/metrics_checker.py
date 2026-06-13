import logging
from typing import Any

from src.api.remnawave_api import RemnawaveAPI
from src.database import get_enabled_nodes, get_thresholds, update_node_metrics

logger = logging.getLogger(__name__)


# Ноды, по которым уже выдан WARNING об отсутствии метрик (чтобы не спамить лог).
_warned_no_metrics: set[str] = set()


def _unwrap_node(data: dict | None) -> dict | None:
    if not isinstance(data, dict):
        return None
    for key in ("node", "item", "data"):
        if isinstance(data.get(key), dict):
            return data[key]
    return data


def _normalize_load(value: Any) -> list[float]:
    if isinstance(value, (int, float)):
        return [float(value), float(value), float(value)]
    if isinstance(value, list):
        result = []
        for item in value[:3]:
            try:
                result.append(float(item))
            except (TypeError, ValueError):
                result.append(0.0)
        return (result + [0.0, 0.0, 0.0])[:3]
    return [0.0, 0.0, 0.0]


def _has_metrics(node: dict | None) -> bool:
    if not node:
        return False
    # Метрики могут лежать в корне объекта ноды (memoryTotal, memoryUsed...)
    # или во вложенном system.info / system.stats (зависит от версии Remnawave API).
    if node.get("memoryTotal") is not None:
        return True
    # Проверяем вложенную структуру response.system
    system = node.get("system")
    if isinstance(system, dict):
        info = system.get("info") or {}
        stats = system.get("stats") or {}
        if info.get("memoryTotal") is not None or stats.get("memoryUsed") is not None or stats.get("memoryFree") is not None:
            return True
    return False


async def fetch_node_metrics(api: RemnawaveAPI, node_uuid: str, base_node: dict | None = None) -> dict | None:
    node = base_node or {}
    if not _has_metrics(node):
        detail = _unwrap_node(await api.get_node(node_uuid))
        if detail:
            merged = dict(node)
            merged.update(detail)
            node = merged

    name = node.get("name", node_uuid[:8]) if node else node_uuid[:8]

    if not _has_metrics(node):
        # Логируем ОДИН раз на ноду, а не каждый раз
        if node_uuid not in _warned_no_metrics:
            _warned_no_metrics.add(node_uuid)
            logger.warning("Node %s: no metrics in API response", name)
        return None
    _warned_no_metrics.discard(node_uuid)

    # Извлекаем метрики из разных структур API (корень или system.info/system.stats)
    system = node.get("system") if isinstance(node.get("system"), dict) else {}
    info = system.get("info") if isinstance(system.get("info"), dict) else {}
    stats = system.get("stats") if isinstance(system.get("stats"), dict) else {}

    try:
        mem_total = int(info.get("memoryTotal") or node.get("memoryTotal") or 0)
        mem_used = int(stats.get("memoryUsed") or node.get("memoryUsed") or 0)
        mem_free = int(stats.get("memoryFree") or node.get("memoryFree") or 0)
        cpus = int(info.get("cpus") or node.get("cpus") or 1)
        load_raw = stats.get("loadAvg") or node.get("loadAvg") or [0, 0, 0]

        if not isinstance(load_raw, list):
            load_raw = [load_raw]

        load_avg = _normalize_load(load_raw)
    except (TypeError, ValueError):
        logger.warning("Node %s: invalid metrics types", name)
        return None

    # Если memoryUsed отсутствует, вычисляем из memoryFree
    if mem_used == 0:
        mem_used = max(mem_total - mem_free, 0)

    if mem_total <= 0:
        logger.warning("Node %s: memoryTotal=0 in API response", name)
        return None

    return {
        "uuid": node_uuid,
        "name": name,
        "cpus": max(cpus, 1),
        "memoryTotal": mem_total,
        "memoryUsed": mem_used,
        "memoryFree": mem_free,
        "loadAvg": load_avg,
        "isConnected": bool(node.get("isConnected")),
        "isDisabled": bool(node.get("isDisabled")),
    }


def bytes_to_mib(value: int) -> float:
    return value / 1024 / 1024


async def check_metrics(api: RemnawaveAPI, alert_engine):
    nodes = await api.get_nodes()
    node_map = {n["uuid"]: n for n in nodes if n.get("uuid")}
    enabled_nodes = await get_enabled_nodes()

    for db_node in enabled_nodes:
        uuid = db_node["uuid"]
        api_node = node_map.get(uuid)
        if not api_node:
            logger.warning("Node %s (uuid=%s) not found in API", db_node["name"], uuid[:8])
            continue

        if api_node.get("isDisabled"):
            logger.info("Node %s disabled, skip metrics", api_node.get("name", uuid[:8]))
            await alert_engine.process("metric", uuid, "high_memory", False)
            await alert_engine.process("metric", uuid, "high_load", False)
            continue
        if not api_node.get("isConnected"):
            logger.info("Node %s not connected, skip metrics", api_node.get("name", uuid[:8]))
            continue

        metrics = await fetch_node_metrics(api, uuid, api_node)
        if not metrics:
            continue

        await update_node_metrics(uuid, metrics)

        mem_total = metrics["memoryTotal"]
        mem_used = metrics["memoryUsed"]
        mem_pct = mem_used / mem_total * 100
        cpus = metrics["cpus"]
        load_avg = metrics["loadAvg"]
        load_per_core = load_avg[0] / cpus

        logger.info(
            "Metrics %s: RAM %.0f/%.0f MiB (%.1f%%), CPU %s, Load %.2f / %.2f / %.2f (%.2f/core)",
            metrics["name"], bytes_to_mib(mem_used), bytes_to_mib(mem_total), mem_pct,
            cpus, load_avg[0], load_avg[1], load_avg[2], load_per_core,
        )

        thresholds = await get_thresholds(uuid)
        high_memory = mem_pct > float(thresholds["memory_percent"])
        await alert_engine.process(
            "metric", uuid, "high_memory", high_memory,
            f"RAM: {mem_pct:.1f}% ({bytes_to_mib(mem_used):.0f}/{bytes_to_mib(mem_total):.0f} MiB, threshold: {thresholds['memory_percent']}%)",
        )

        high_load = load_per_core > float(thresholds["load_per_core"])
        await alert_engine.process(
            "metric", uuid, "high_load", high_load,
            f"Load: {load_per_core:.2f}/core (threshold: {thresholds['load_per_core']})",
        )

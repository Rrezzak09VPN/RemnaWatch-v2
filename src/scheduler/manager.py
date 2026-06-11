import asyncio
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import get_setting

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None
_api_ref = None
_alert_engine_ref = None
_locks: dict[str, asyncio.Lock] = {}


def init_scheduler(api, alert_engine):
    global scheduler, _api_ref, _alert_engine_ref
    _api_ref = api
    _alert_engine_ref = alert_engine
    scheduler = AsyncIOScheduler()
    return scheduler


def _lock(name: str) -> asyncio.Lock:
    if name not in _locks:
        _locks[name] = asyncio.Lock()
    return _locks[name]


async def _run_locked(name: str, func, *args):
    lock = _lock(name)
    if lock.locked():
        logger.warning("Job %s is already running, skipping overlapping run", name)
        return
    async with lock:
        try:
            await func(*args)
        except Exception:
            logger.exception("Job %s failed", name)


async def _intervals() -> dict[str, int]:
    return {
        "check_nodes": int(await get_setting("nodes_interval_seconds") or 60),
        "check_metrics": int(await get_setting("metrics_interval_seconds") or 60),
        "check_traffic": int(await get_setting("traffic_interval_seconds") or 120),
        "check_inbounds": int(await get_setting("inbounds_interval_seconds") or 300),
        "discovery": int(await get_setting("discovery_interval_seconds") or 600),
    }


async def start_scheduler():
    if scheduler is None:
        logger.error("Scheduler not initialized")
        return

    from src.checks.inbound_checker import check_inbounds
    from src.checks.metrics_checker import check_metrics
    from src.checks.nodes_checker import check_nodes
    from src.checks.traffic_checker import check_traffic
    from src.discovery import run_discovery

    intervals = await _intervals()
    jobs = {
        "check_nodes": (check_nodes, [_api_ref, _alert_engine_ref], "Nodes check"),
        "check_metrics": (check_metrics, [_api_ref, _alert_engine_ref], "Metrics check"),
        "check_traffic": (check_traffic, [_api_ref, _alert_engine_ref], "Traffic check"),
        "check_inbounds": (check_inbounds, [_api_ref, _alert_engine_ref], "Inbounds check"),
        "discovery": (run_discovery, [_api_ref], "Discovery"),
    }
    for job_id, (func, args, name) in jobs.items():
        scheduler.add_job(
            _run_locked,
            "interval",
            seconds=intervals[job_id],
            args=[job_id, func, *args],
            id=job_id,
            replace_existing=True,
            name=name,
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()
    logger.info("Scheduler started: %s", ", ".join(f"{k}={v}s" for k, v in intervals.items()))


async def reschedule_jobs():
    if scheduler is None:
        logger.warning("Scheduler not initialized for reschedule")
        return
    intervals = await _intervals()
    for job_id, seconds in intervals.items():
        if scheduler.get_job(job_id):
            scheduler.reschedule_job(job_id, trigger="interval", seconds=seconds)
    logger.info("Scheduler rescheduled: %s", ", ".join(f"{k}={v}s" for k, v in intervals.items()))


async def trigger_all_checks():
    if _api_ref is None or _alert_engine_ref is None:
        logger.error("API or AlertEngine not set")
        return

    from src.checks.inbound_checker import check_inbounds
    from src.checks.metrics_checker import check_metrics
    from src.checks.nodes_checker import check_nodes
    from src.checks.traffic_checker import check_traffic
    from src.discovery import run_discovery

    await _run_locked("discovery", run_discovery, _api_ref)
    await _run_locked("check_nodes", check_nodes, _api_ref, _alert_engine_ref)
    await _run_locked("check_metrics", check_metrics, _api_ref, _alert_engine_ref)
    await _run_locked("check_traffic", check_traffic, _api_ref, _alert_engine_ref)
    await _run_locked("check_inbounds", check_inbounds, _api_ref, _alert_engine_ref)
    logger.info("All checks triggered manually")


async def stop_scheduler():
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

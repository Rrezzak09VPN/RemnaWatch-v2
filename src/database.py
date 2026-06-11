import logging
import sqlite3
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH: Optional[str] = None


def get_db_path() -> str:
    global DB_PATH
    if DB_PATH is None:
        from src.config import settings
        DB_PATH = settings.db_path
    return DB_PATH


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(get_db_path())
    db.row_factory = dict_factory
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    enabled BOOLEAN DEFAULT 0,
    ignored BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0,
    last_status TEXT,
    expected_ip TEXT,
    last_check TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threshold_memory_percent INTEGER DEFAULT 90,
    threshold_load_per_core REAL DEFAULT 1.5,
    traffic_used_bytes INTEGER DEFAULT 0,
    traffic_limit_bytes INTEGER DEFAULT 0,
    traffic_reset_day INTEGER,
    is_traffic_tracking_active BOOLEAN DEFAULT 0,
    cpus INTEGER,
    memory_total_bytes INTEGER,
    memory_used_bytes INTEGER,
    memory_free_bytes INTEGER,
    load_avg_1 REAL,
    load_avg_5 REAL,
    load_avg_15 REAL,
    view_position INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS inbounds (
    uuid TEXT PRIMARY KEY,
    remark TEXT,
    server TEXT,
    port INTEGER,
    protocol TEXT,
    network TEXT,
    security TEXT,
    node_uuid TEXT,
    config_inbound_uuid TEXT,
    enabled BOOLEAN DEFAULT 0,
    ignored BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0,
    last_status TEXT,
    last_ip TEXT,
    last_check TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sni TEXT,
    fingerprint TEXT,
    host TEXT,
    path TEXT,
    alpn TEXT,
    allow_insecure BOOLEAN DEFAULT 0,
    is_disabled BOOLEAN DEFAULT 0,
    security_layer TEXT,
    expected_ip TEXT,
    last_error TEXT,
    view_position INTEGER DEFAULT 0,
    FOREIGN KEY (node_uuid) REFERENCES nodes(uuid)
);

CREATE TABLE IF NOT EXISTS incidents (
    object_type TEXT,
    object_uuid TEXT,
    incident_type TEXT,
    consecutive_fails INTEGER DEFAULT 0,
    consecutive_successes INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 0,
    last_alert_ts TIMESTAMP,
    PRIMARY KEY (object_type, object_uuid, incident_type)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    object_type TEXT,
    object_uuid TEXT,
    incident_type TEXT,
    message TEXT,
    resolved BOOLEAN DEFAULT 0
);
"""

DEFAULT_SETTINGS = {
    "nodes_interval_seconds": "60",
    "metrics_interval_seconds": "60",
    "traffic_interval_seconds": "120",
    "inbounds_interval_seconds": "300",
    "discovery_interval_seconds": "600",
    "singbox_parallel_count": "2",
    "fail_threshold": "3",
    "recovery_threshold": "2",
    "alert_cooldown_seconds": "3600",
    "traffic_warn_percent": "90",
}

MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "nodes": [
        ("traffic_used_bytes", "INTEGER DEFAULT 0"),
        ("traffic_limit_bytes", "INTEGER DEFAULT 0"),
        ("traffic_reset_day", "INTEGER"),
        ("is_traffic_tracking_active", "BOOLEAN DEFAULT 0"),
        ("cpus", "INTEGER"),
        ("memory_total_bytes", "INTEGER"),
        ("memory_used_bytes", "INTEGER"),
        ("memory_free_bytes", "INTEGER"),
        ("load_avg_1", "REAL"),
        ("load_avg_5", "REAL"),
        ("load_avg_15", "REAL"),
        ("view_position", "INTEGER DEFAULT 0"),
    ],
    "inbounds": [
        ("sni", "TEXT"),
        ("fingerprint", "TEXT"),
        ("host", "TEXT"),
        ("path", "TEXT"),
        ("alpn", "TEXT"),
        ("allow_insecure", "BOOLEAN DEFAULT 0"),
        ("is_disabled", "BOOLEAN DEFAULT 0"),
        ("security_layer", "TEXT"),
        ("expected_ip", "TEXT"),
        ("last_error", "TEXT"),
        ("view_position", "INTEGER DEFAULT 0"),
    ],
}


async def _ensure_columns(db: aiosqlite.Connection):
    for table, columns in MIGRATIONS.items():
        cursor = await db.execute(f"PRAGMA table_info({table})")
        existing = {row["name"] for row in await cursor.fetchall()}
        for name, definition in columns:
            if name not in existing:
                logger.info("DB migration: adding %s.%s", table, name)
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


async def init_db():
    Path(get_db_path()).parent.mkdir(parents=True, exist_ok=True)
    db = await get_db()
    try:
        for stmt in SCHEMA_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                await db.execute(stmt)
        await _ensure_columns(db)
        for key, value in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        await db.commit()
    finally:
        await db.close()


async def get_setting(key: str) -> str:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else DEFAULT_SETTINGS.get(key, "")
    finally:
        await db.close()


async def set_setting(key: str, value: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def get_all_settings() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        result = dict(DEFAULT_SETTINGS)
        for row in rows:
            result[row["key"]] = row["value"]
        return result
    finally:
        await db.close()


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _load_values(node: dict):
    system = node.get("system") if isinstance(node.get("system"), dict) else {}
    load = node.get("loadAvg") or system.get("loadAvg") or []
    if not isinstance(load, list):
        load = []
    load = (load + [None, None, None])[:3]
    return load


async def upsert_node(node: dict):
    db = await get_db()
    try:
        load = _load_values(node)
        system = node.get("system") if isinstance(node.get("system"), dict) else {}
        await db.execute(
            """INSERT INTO nodes (
                   uuid, name, address, expected_ip,
                   traffic_used_bytes, traffic_limit_bytes, traffic_reset_day, is_traffic_tracking_active,
                   cpus, memory_total_bytes, memory_used_bytes, memory_free_bytes,
                   load_avg_1, load_avg_5, load_avg_15, view_position, archived
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
               ON CONFLICT(uuid) DO UPDATE SET
                   name=excluded.name,
                   address=excluded.address,
                   expected_ip=excluded.expected_ip,
                   traffic_used_bytes=excluded.traffic_used_bytes,
                   traffic_limit_bytes=excluded.traffic_limit_bytes,
                   traffic_reset_day=excluded.traffic_reset_day,
                   is_traffic_tracking_active=excluded.is_traffic_tracking_active,
                   cpus=excluded.cpus,
                   memory_total_bytes=excluded.memory_total_bytes,
                   memory_used_bytes=excluded.memory_used_bytes,
                   memory_free_bytes=excluded.memory_free_bytes,
                   load_avg_1=excluded.load_avg_1,
                   load_avg_5=excluded.load_avg_5,
                   load_avg_15=excluded.load_avg_15,
                   view_position=excluded.view_position,
                   archived=0""",
            (
                node["uuid"],
                node.get("name") or node["uuid"][:8],
                node.get("address", ""),
                node.get("address", ""),
                _as_int(node.get("trafficUsedBytes"), 0),
                _as_int(node.get("trafficLimitBytes"), 0),
                node.get("trafficResetDay"),
                int(bool(node.get("isTrafficTrackingActive"))),
                node.get("cpus") or system.get("cpus"),
                node.get("memoryTotal") or system.get("memoryTotal"),
                node.get("memoryUsed") or system.get("memoryUsed"),
                node.get("memoryFree") or system.get("memoryFree"),
                load[0], load[1], load[2],
                _as_int(node.get("viewPosition"), 0),
            ),
        )
        await db.commit()
        logger.info("Node upserted: %s (%s)", node.get("name", node["uuid"][:8]), node["uuid"][:8])
    except Exception as e:
        logger.exception("Failed to upsert node %s: %s", node.get("uuid", "unknown"), e)
    finally:
        await db.close()


async def update_node_metrics(uuid: str, metrics: dict):
    db = await get_db()
    try:
        load = metrics.get("loadAvg") or [None, None, None]
        load = (load + [None, None, None])[:3]
        await db.execute(
            """UPDATE nodes SET
               cpus=?, memory_total_bytes=?, memory_used_bytes=?, memory_free_bytes=?,
               load_avg_1=?, load_avg_5=?, load_avg_15=?, last_check=CURRENT_TIMESTAMP
               WHERE uuid=?""",
            (
                metrics.get("cpus"), metrics.get("memoryTotal"), metrics.get("memoryUsed"), metrics.get("memoryFree"),
                load[0], load[1], load[2], uuid,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def update_node_traffic(uuid: str, node: dict):
    db = await get_db()
    try:
        await db.execute(
            """UPDATE nodes SET
               traffic_used_bytes=?, traffic_limit_bytes=?, traffic_reset_day=?, is_traffic_tracking_active=?
               WHERE uuid=?""",
            (
                _as_int(node.get("trafficUsedBytes"), 0),
                _as_int(node.get("trafficLimitBytes"), 0),
                node.get("trafficResetDay"),
                int(bool(node.get("isTrafficTrackingActive"))),
                uuid,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def upsert_host(host: dict, config_inbound: dict | None, inbound_uuid: str = ""):
    db = await get_db()
    try:
        remark = host.get("remark") or host.get("tag") or host["uuid"][:8]
        cfg_uuid = inbound_uuid or (config_inbound.get("uuid", "") if config_inbound else "")
        raw = (config_inbound or {}).get("rawInbound") or {}
        ss = raw.get("streamSettings") or {}
        protocol = (config_inbound or {}).get("protocol") or (config_inbound or {}).get("type") or raw.get("protocol") or ""
        network = (config_inbound or {}).get("network") or ss.get("network") or ""
        security = (config_inbound or {}).get("security") or ss.get("security") or ""
        nodes = host.get("nodes") or []
        node_uuid = nodes[0] if nodes else None
        alpn = host.get("alpn")
        if isinstance(alpn, list):
            alpn = ",".join(map(str, alpn))

        await db.execute(
            """INSERT INTO inbounds (
                   uuid, remark, server, port, protocol, network, security, config_inbound_uuid, node_uuid,
                   sni, fingerprint, host, path, alpn, allow_insecure, is_disabled, security_layer, expected_ip,
                   view_position, archived
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
               ON CONFLICT(uuid) DO UPDATE SET
                   remark=excluded.remark,
                   server=excluded.server,
                   port=excluded.port,
                   protocol=excluded.protocol,
                   network=excluded.network,
                   security=excluded.security,
                   config_inbound_uuid=excluded.config_inbound_uuid,
                   node_uuid=excluded.node_uuid,
                   sni=excluded.sni,
                   fingerprint=excluded.fingerprint,
                   host=excluded.host,
                   path=excluded.path,
                   alpn=excluded.alpn,
                   allow_insecure=excluded.allow_insecure,
                   is_disabled=excluded.is_disabled,
                   security_layer=excluded.security_layer,
                   expected_ip=excluded.expected_ip,
                   view_position=excluded.view_position,
                   archived=0""",
            (
                host["uuid"], remark, host.get("address", ""), host.get("port", 0),
                protocol, network, security, cfg_uuid, node_uuid,
                host.get("sni") or "", host.get("fingerprint") or "firefox",
                host.get("host") or "", host.get("path") or "", alpn or "",
                int(bool(host.get("allowInsecure"))), int(bool(host.get("isDisabled"))),
                host.get("securityLayer") or "", host.get("expectedIp") or "",
                _as_int(host.get("viewPosition"), 0),
            ),
        )
        await db.commit()
        logger.info("Host upserted: %s (%s/%s, config=%s)", remark, protocol, network, cfg_uuid[:8] if cfg_uuid else "none")
    except Exception as e:
        logger.exception("Failed to upsert host %s: %s", host.get("uuid", "unknown"), e)
    finally:
        await db.close()


async def get_all_nodes() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM nodes WHERE archived=0 ORDER BY view_position, name")
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_enabled_nodes() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM nodes WHERE enabled=1 AND ignored=0 AND archived=0 ORDER BY view_position, name")
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_all_inbounds() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM inbounds WHERE archived=0 ORDER BY view_position, remark")
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_enabled_inbounds() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM inbounds WHERE enabled=1 AND ignored=0 AND archived=0 ORDER BY view_position, remark")
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_enabled_inbounds_ordered() -> list[dict]:
    """Возвращает список включённых inbound'ов, отсортированных по view_position ноды,
    затем по view_position самого inbound'а (порядок панели Remnawave).

    LEFT JOIN вместо INNER JOIN: node_uuid у хоста может быть NULL (host из /api/hosts
    не всегда привязан к ноде) — такие inbound'ы не должны выпадать из проверки.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT i.*, COALESCE(n.view_position, 0) AS node_view_position
               FROM inbounds i
               LEFT JOIN nodes n ON i.node_uuid = n.uuid
               WHERE i.enabled = 1 AND i.ignored = 0 AND i.archived = 0
               ORDER BY COALESCE(n.view_position, 0), i.view_position, i.remark"""
        )
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def get_inbound_by_uuid(uuid: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM inbounds WHERE uuid=?", (uuid,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_enabled_inbound_uuids() -> set[str]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT uuid FROM inbounds WHERE enabled=1 AND ignored=0 AND archived=0")
        rows = await cursor.fetchall()
        return {row["uuid"] for row in rows}
    finally:
        await db.close()


async def update_node_status(uuid: str, status: str):
    db = await get_db()
    try:
        await db.execute("UPDATE nodes SET last_status=?, last_check=CURRENT_TIMESTAMP WHERE uuid=?", (status, uuid))
        await db.commit()
    finally:
        await db.close()


async def update_inbound_status(uuid: str, status: str, ip: str = "", error: str = ""):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE inbounds SET last_status=?, last_ip=?, last_error=?, last_check=CURRENT_TIMESTAMP WHERE uuid=?",
            (status, ip, error[:1000] if error else "", uuid),
        )
        await db.commit()
    finally:
        await db.close()


async def toggle_node_enabled(uuid: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT enabled FROM nodes WHERE uuid=?", (uuid,))
        row = await cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row["enabled"] else 1
        await db.execute("UPDATE nodes SET enabled=? WHERE uuid=?", (new_val, uuid))
        await db.commit()
        return bool(new_val)
    finally:
        await db.close()


async def toggle_inbound_enabled(uuid: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT enabled FROM inbounds WHERE uuid=?", (uuid,))
        row = await cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row["enabled"] else 1
        await db.execute("UPDATE inbounds SET enabled=? WHERE uuid=?", (new_val, uuid))
        await db.commit()
        return bool(new_val)
    finally:
        await db.close()


async def ignore_object(obj_type: str, uuid: str):
    table = "nodes" if obj_type == "node" else "inbounds"
    db = await get_db()
    try:
        await db.execute(f"UPDATE {table} SET ignored=1 WHERE uuid=?", (uuid,))
        await db.commit()
    finally:
        await db.close()


async def get_uuids_set(table: str) -> set[str]:
    if table not in {"nodes", "inbounds"}:
        raise ValueError("invalid table")
    db = await get_db()
    try:
        cursor = await db.execute(f"SELECT uuid FROM {table} WHERE archived=0")
        rows = await cursor.fetchall()
        return {row["uuid"] for row in rows}
    finally:
        await db.close()


async def archive_object(table: str, uuid: str):
    if table not in {"nodes", "inbounds"}:
        raise ValueError("invalid table")
    db = await get_db()
    try:
        await db.execute(f"UPDATE {table} SET archived=1 WHERE uuid=?", (uuid,))
        await db.commit()
    finally:
        await db.close()


async def get_or_create_incident(obj_type: str, obj_uuid: str, incident_type: str) -> dict:
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO incidents (object_type, object_uuid, incident_type)
               VALUES (?, ?, ?)""",
            (obj_type, obj_uuid, incident_type),
        )
        await db.commit()
        cursor = await db.execute(
            """SELECT * FROM incidents
               WHERE object_type=? AND object_uuid=? AND incident_type=?""",
            (obj_type, obj_uuid, incident_type),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("failed to create incident row")
        return row
    finally:
        await db.close()


async def update_incident(
    obj_type: str,
    obj_uuid: str,
    incident_type: str,
    fails: int,
    successes: int,
    is_active: bool,
    last_alert_ts: str | None = None,
):
    db = await get_db()
    try:
        await db.execute(
            """UPDATE incidents SET
               consecutive_fails=?, consecutive_successes=?, is_active=?, last_alert_ts=?
               WHERE object_type=? AND object_uuid=? AND incident_type=?""",
            (fails, successes, int(is_active), last_alert_ts, obj_type, obj_uuid, incident_type),
        )
        await db.commit()
    finally:
        await db.close()


async def log_alert(obj_type: str, obj_uuid: str, incident_type: str, message: str, resolved: bool = False):
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO alerts_history (object_type, object_uuid, incident_type, message, resolved)
               VALUES (?, ?, ?, ?, ?)""",
            (obj_type, obj_uuid, incident_type, message, int(resolved)),
        )
        await db.commit()
    finally:
        await db.close()


async def get_recent_alerts(limit: int = 20) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM alerts_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_thresholds(node_uuid: str) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT threshold_memory_percent, threshold_load_per_core FROM nodes WHERE uuid=?",
            (node_uuid,),
        )
        row = await cursor.fetchone()
        if row:
            return {
                "memory_percent": row["threshold_memory_percent"],
                "load_per_core": row["threshold_load_per_core"],
            }
        return {"memory_percent": 90, "load_per_core": 1.5}
    finally:
        await db.close()


async def set_threshold(node_uuid: str, key: str, value):
    col = "threshold_memory_percent" if key == "memory_percent" else "threshold_load_per_core"
    db = await get_db()
    try:
        await db.execute(f"UPDATE nodes SET {col}=? WHERE uuid=?", (value, node_uuid))
        await db.commit()
    finally:
        await db.close()


async def get_new_objects() -> list[dict]:
    result: list[dict] = []
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT uuid, name as name, 'node' as obj_type FROM nodes WHERE enabled=0 AND ignored=0 AND archived=0"
        )
        result.extend(await cursor.fetchall())
        cursor = await db.execute(
            "SELECT uuid, remark as name, 'inbound' as obj_type FROM inbounds WHERE enabled=0 AND ignored=0 AND archived=0"
        )
        result.extend(await cursor.fetchall())
        return result
    finally:
        await db.close()

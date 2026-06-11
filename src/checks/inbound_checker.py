import asyncio
import logging
from dataclasses import dataclass

from src.api.remnawave_api import RemnawaveAPI
from src.checks.probe import check_connectivity, resolve_host_ips
from src.checks.singbox_runner import SingBoxRunner
from src.config import settings
from src.crypto.x25519 import compute_public_key
from src.database import get_enabled_inbounds, get_setting, update_inbound_status

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    status: str
    ip: str = ""
    error: str = ""


def _base_config() -> dict:
    return {
        "log": {"level": "error"},
        "inbounds": [{"type": "socks", "listen": "127.0.0.1", "listen_port": 0}],
    }


def _raw(config_inbound: dict) -> dict:
    return config_inbound.get("rawInbound") or {}


def _stream(config_inbound: dict) -> dict:
    return _raw(config_inbound).get("streamSettings") or {}


def _extract_protocol(config_inbound: dict, host: dict | None = None) -> str:
    raw = _raw(config_inbound)
    host = host or {}
    return (
        config_inbound.get("protocol")
        or config_inbound.get("type")
        or raw.get("protocol")
        or host.get("protocol")
        or ""
    ).lower()


def _extract_network(config_inbound: dict, host: dict | None = None) -> str:
    ss = _stream(config_inbound)
    host = host or {}
    return (
        config_inbound.get("network")
        or ss.get("network")
        or host.get("network")
        or ""
    ).lower()


def _extract_security(config_inbound: dict, host: dict | None = None) -> str:
    ss = _stream(config_inbound)
    host = host or {}
    return (
        config_inbound.get("security")
        or ss.get("security")
        or host.get("security")
        or ""
    ).lower()


def _host_info(host: dict, config_inbound: dict) -> dict:
    ss = _stream(config_inbound)
    reality = ss.get("realitySettings") or {}
    server_names = reality.get("serverNames") or []
    server = host.get("server") or host.get("address") or ""
    sni = host.get("sni") or (server_names[0] if server_names else "") or server
    fingerprint = host.get("fingerprint") or "firefox"
    return {
        "server": server,
        "port": int(host.get("port") or _raw(config_inbound).get("port") or config_inbound.get("port") or 443),
        "sni": sni,
        "fingerprint": fingerprint,
        "allow_insecure": bool(host.get("allow_insecure") or host.get("allowInsecure")),
    }


def _reality_keys(config_inbound: dict) -> tuple[str, str]:
    reality = _stream(config_inbound).get("realitySettings") or {}
    private_key = reality.get("privateKey") or ""
    if not private_key:
        raise ValueError("missing reality privateKey")
    public_key = compute_public_key(private_key)
    short_ids = reality.get("shortIds") or []
    short_id = short_ids[0] if short_ids else ""
    return public_key, short_id


def build_vless_tcp_config(host: dict, vless_uuid: str, public_key: str, short_id: str) -> dict:
    return {
        **_base_config(),
        "outbounds": [{
            "type": "vless",
            "server": host["server"],
            "server_port": host["port"],
            "uuid": vless_uuid,
            "flow": "xtls-rprx-vision",
            "tls": {
                "enabled": True,
                "server_name": host["sni"],
                "reality": {"enabled": True, "public_key": public_key, "short_id": short_id},
                "utls": {"enabled": True, "fingerprint": host["fingerprint"]},
            },
        }],
    }


def build_vless_grpc_config(host: dict, vless_uuid: str, public_key: str, service_name: str, short_id: str) -> dict:
    return {
        **_base_config(),
        "outbounds": [{
            "type": "vless",
            "server": host["server"],
            "server_port": host["port"],
            "uuid": vless_uuid,
            "flow": "",
            "tls": {
                "enabled": True,
                "server_name": host["sni"],
                "reality": {"enabled": True, "public_key": public_key, "short_id": short_id},
                "utls": {"enabled": True, "fingerprint": host["fingerprint"]},
            },
            "transport": {"type": "grpc", "service_name": service_name},
        }],
    }


def build_hysteria2_config(host: dict, password: str) -> dict:
    return {
        **_base_config(),
        "outbounds": [{
            "type": "hysteria2",
            "server": host["server"],
            "server_port": host["port"],
            "password": password,
            "tls": {
                "enabled": True,
                "server_name": host["sni"],
                # Remnawave Hysteria2 often uses a generated cert on node side.
                "insecure": True,
                "alpn": ["h3"],
            },
        }],
    }


def build_singbox_config(host: dict, config_inbound: dict, vless_uuid: str) -> dict | None:
    protocol = _extract_protocol(config_inbound, host)
    network = _extract_network(config_inbound, host)
    security = _extract_security(config_inbound, host)
    info = _host_info(host, config_inbound)

    logger.info(
        "Building sing-box config for %s: protocol=%s, network=%s, security=%s, sni=%s, fingerprint=%s",
        host.get("remark") or host.get("uuid", "unknown")[:8], protocol, network, security, info["sni"], info["fingerprint"],
    )

    if not info["server"]:
        raise ValueError("host server/address is empty")

    if network == "xhttp":
        logger.warning("Skipping XHTTP inbound %s: not supported by sing-box", host.get("remark", host.get("uuid", "unknown")[:8]))
        return None

    if protocol == "vless" and security == "reality" and network == "tcp":
        public_key, short_id = _reality_keys(config_inbound)
        return build_vless_tcp_config(info, vless_uuid, public_key, short_id)

    if protocol == "vless" and security == "reality" and network == "grpc":
        public_key, short_id = _reality_keys(config_inbound)
        service_name = (_stream(config_inbound).get("grpcSettings") or {}).get("serviceName") or ""
        if not service_name:
            raise ValueError("missing grpc serviceName")
        return build_vless_grpc_config(info, vless_uuid, public_key, service_name, short_id)

    if protocol in {"hysteria", "hysteria2"} or network in {"hysteria", "hysteria2"}:
        return build_hysteria2_config(info, vless_uuid)

    logger.warning("Unsupported protocol/network/security: %s/%s/%s", protocol, network, security)
    return None


async def _ip_matches(host: dict, ip: str | None) -> bool:
    if not ip:
        return True
    expected = (host.get("expected_ip") or "").strip()
    if expected:
        return ip == expected
    server = host.get("server") or host.get("address") or ""
    resolved = await resolve_host_ips(server)
    if not resolved:
        return True
    return ip in resolved


async def check_inbound(
    inbound: dict,
    config_inbound: dict | None,
    api: RemnawaveAPI,
    runner: SingBoxRunner,
    semaphore: asyncio.Semaphore,
    monitor_user: dict,
) -> CheckResult:
    async with semaphore:
        name = inbound.get("remark") or inbound.get("uuid", "unknown")[:8]
        try:
            if inbound.get("is_disabled"):
                await update_inbound_status(inbound["uuid"], "DISABLED", "", "host disabled in Remnawave")
                logger.info("Inbound %s skipped: host disabled in Remnawave", name)
                return CheckResult("DISABLED")

            if not config_inbound:
                error = f"config_inbound_uuid={inbound.get('config_inbound_uuid')} not found"
                await update_inbound_status(inbound["uuid"], "CONFIG_ERROR", "", error)
                logger.warning("Inbound %s: %s", name, error)
                return CheckResult("CONFIG_ERROR", error=error)

            vless_uuid = monitor_user.get("vlessUuid") or monitor_user.get("vless_uuid")
            if not vless_uuid:
                error = "monitoring user has no vlessUuid"
                await update_inbound_status(inbound["uuid"], "CONFIG_ERROR", "", error)
                return CheckResult("CONFIG_ERROR", error=error)

            singbox_cfg = build_singbox_config(inbound, config_inbound, vless_uuid)
            if singbox_cfg is None:
                await update_inbound_status(inbound["uuid"], "SKIPPED_UNSUPPORTED", "", "unsupported by sing-box")
                return CheckResult("SKIPPED_UNSUPPORTED")

            async with runner.run(singbox_cfg, label=name) as (port, _proc):
                ok, ip, error = await check_connectivity(f"127.0.0.1:{port}")
                if not ok:
                    status = "BROKEN"
                elif not await _ip_matches(inbound, ip):
                    status = "WARNING"
                    error = f"wrong exit ip: got {ip}, expected {inbound.get('expected_ip') or inbound.get('server')}"
                else:
                    status = "HEALTHY"

                await update_inbound_status(inbound["uuid"], status, ip or "", error)
                logger.info("Inbound %s: %s (IP: %s) %s", name, status, ip or "-", error or "")
                return CheckResult(status, ip or "", error or "")

        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            logger.exception("Inbound %s check failed: %s", name, error)
            await update_inbound_status(inbound["uuid"], "BROKEN", "", error)
            return CheckResult("BROKEN", error=error)


async def check_inbounds(api: RemnawaveAPI, alert_engine):
    inbounds = await get_enabled_inbounds()
    if not inbounds:
        logger.info("No enabled inbounds for check")
        return

    monitor_user = await api.get_user(settings.monitor_user_uuid)
    if not monitor_user:
        logger.error("Monitoring user %s not found", settings.monitor_user_uuid)
        return
    if monitor_user.get("status") and monitor_user.get("status") != "ACTIVE":
        logger.warning("Monitoring user %s is not ACTIVE: %s", settings.monitor_user_uuid, monitor_user.get("status"))

    config_map = await api.get_all_config_inbounds_map()
    logger.info("Inbound check started: %s hosts, %s config inbounds", len(inbounds), len(config_map))

    parallel_count = max(1, int(await get_setting("singbox_parallel_count") or 1))
    semaphore = asyncio.Semaphore(parallel_count)
    runner = SingBoxRunner(settings.singbox_bin)

    tasks = [
        check_inbound(
            ib,
            config_map.get(str(ib.get("config_inbound_uuid") or "").lower()),
            api,
            runner,
            semaphore,
            monitor_user,
        )
        for ib in inbounds
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    checked = skipped = broken = warnings = 0
    for inbound, result in zip(inbounds, results):
        if isinstance(result, Exception):
            logger.exception("Inbound %s task crashed", inbound.get("remark", inbound["uuid"][:8]), exc_info=result)
            await alert_engine.process("inbound", inbound["uuid"], "broken", True, str(result))
            broken += 1
            continue

        if result.status in {"HEALTHY", "WARNING", "BROKEN"}:
            checked += 1
        else:
            skipped += 1

        is_broken = result.status == "BROKEN"
        is_wrong_ip = result.status == "WARNING"
        if is_broken:
            broken += 1
        if is_wrong_ip:
            warnings += 1

        await alert_engine.process("inbound", inbound["uuid"], "broken", is_broken, result.error)
        await alert_engine.process("inbound", inbound["uuid"], "wrong_ip", is_wrong_ip, result.error)

    logger.info(
        "Inbound check complete: %s checked, %s skipped, %s broken, %s warnings",
        checked, skipped, broken, warnings,
    )

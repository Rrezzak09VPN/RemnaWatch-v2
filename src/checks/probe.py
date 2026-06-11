import asyncio
import logging
import socket
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GENERATE_204_URLS = [
    "https://cp.cloudflare.com/generate_204",
    "https://connectivitycheck.gstatic.com/generate_204",
    "https://www.apple.com/library/test/success.html",
]

IP_SERVICES = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
    "https://ipapi.co/ip",
]


async def check_connectivity(proxy: str) -> tuple[bool, Optional[str], str]:
    last_error = ""
    for url in GENERATE_204_URLS:
        try:
            async with httpx.AsyncClient(
                proxies={"all://": f"socks5://{proxy}"},
                timeout=10.0,
                verify=False,
            ) as client:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code in (200, 204):
                    ip = await get_ip_via_proxy(proxy)
                    return True, ip, ""
                last_error = f"{url} returned HTTP {resp.status_code}"
        except Exception as e:
            last_error = f"{url}: {type(e).__name__}: {e}"
            logger.debug("Connectivity probe failed via %s at %s: %s", proxy, url, e)
    return False, None, last_error


async def get_ip_via_proxy(proxy: str) -> Optional[str]:
    for service in IP_SERVICES:
        try:
            async with httpx.AsyncClient(
                proxies={"all://": f"socks5://{proxy}"},
                timeout=10.0,
                verify=False,
            ) as client:
                resp = await client.get(service, follow_redirects=True)
                if resp.status_code == 200:
                    ip = resp.text.strip()
                    if ip:
                        return ip
        except Exception as e:
            logger.debug("IP service failed via %s at %s: %s", proxy, service, e)
    return None


async def resolve_host_ips(host: str) -> set[str]:
    if not host:
        return set()
    try:
        socket.inet_pton(socket.AF_INET, host)
        return {host}
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return {host}
    except OSError:
        pass

    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        return {item[4][0] for item in infos if item and item[4]}
    except Exception as e:
        logger.debug("Failed to resolve %s: %s", host, e)
        return set()

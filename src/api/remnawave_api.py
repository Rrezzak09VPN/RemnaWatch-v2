import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RemnawaveAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.token}"},
            verify=False,
            timeout=30.0,
        )

    async def close(self):
        await self.client.aclose()

    async def _get_raw(self, path: str) -> Any | None:
        try:
            resp = await self.client.get(path)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("API request failed: %s - %s", path, e)
            return None
        except Exception as e:
            logger.exception("Unexpected API error: %s - %s", path, e)
            return None

    async def _get(self, path: str) -> list[dict] | dict | None:
        data = await self._get_raw(path)
        if data is None:
            return None

        logger.debug("API %s response type: %s", path, type(data).__name__)
        if isinstance(data, dict):
            logger.debug("API %s response keys: %s", path, list(data.keys()))
            if "response" in data:
                result = data["response"]
                logger.debug(
                    "API %s .response type: %s, count: %s",
                    path,
                    type(result).__name__,
                    len(result) if isinstance(result, list) else "N/A",
                )
                return result
            for key in ("nodes", "users", "inbounds", "hosts"):
                if key in data:
                    return data[key]
        elif isinstance(data, list):
            logger.debug("API %s returned list with %s items", path, len(data))
        return data

    async def get_nodes(self) -> list[dict]:
        data = await self._get("/api/nodes")
        return data if isinstance(data, list) else []

    async def get_node(self, uuid: str) -> dict | None:
        data = await self._get(f"/api/nodes/{uuid}")
        return data if isinstance(data, dict) else None

    async def get_users(self) -> list[dict]:
        data = await self._get("/api/users")
        if isinstance(data, dict) and "users" in data:
            return data["users"] if isinstance(data["users"], list) else []
        return data if isinstance(data, list) else []

    async def get_user(self, uuid: str) -> dict | None:
        # Remnawave installations differ: some support /api/users/{uuid}, some only /api/users.
        data = await self._get(f"/api/users/{uuid}")
        if isinstance(data, dict):
            return data
        users = await self.get_users()
        uuid_lower = uuid.lower()
        for user in users:
            if str(user.get("uuid", "")).lower() == uuid_lower:
                return user
        return None

    async def get_inbounds(self) -> list[dict]:
        data = await self._get("/api/config-profiles/inbounds")
        if isinstance(data, dict):
            for key in ("inbounds", "items", "data"):
                val = data.get(key)
                if isinstance(val, list):
                    return val
        return data if isinstance(data, list) else []

    async def get_hosts(self) -> list[dict]:
        data = await self._get("/api/hosts")
        if isinstance(data, dict) and "hosts" in data:
            return data["hosts"] if isinstance(data["hosts"], list) else []
        return data if isinstance(data, list) else []

    async def get_config_inbound(self, uuid: str) -> dict | None:
        if not uuid:
            return None
        uuid_lower = uuid.lower()

        # Main source: /api/config-profiles/inbounds.
        inbounds = await self.get_inbounds()
        for ib in inbounds:
            if str(ib.get("uuid", "")).lower() == uuid_lower:
                return ib
            raw = ib.get("rawInbound") or {}
            if str(raw.get("uuid", "")).lower() == uuid_lower:
                return ib

        # Fallback source confirmed by manual tests: node.configProfile.activeInbounds.
        nodes = await self.get_nodes()
        for node in nodes:
            active = (node.get("configProfile") or {}).get("activeInbounds") or []
            for ib in active:
                if str(ib.get("uuid", "")).lower() == uuid_lower:
                    return ib
        return None

    async def get_all_config_inbounds_map(self) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for ib in await self.get_inbounds():
            uuid = str(ib.get("uuid", "")).lower()
            if uuid:
                result[uuid] = ib

        # Merge node activeInbounds too. Do not overwrite explicit endpoint values.
        for node in await self.get_nodes():
            for ib in (node.get("configProfile") or {}).get("activeInbounds") or []:
                uuid = str(ib.get("uuid", "")).lower()
                if uuid and uuid not in result:
                    result[uuid] = ib
        return result

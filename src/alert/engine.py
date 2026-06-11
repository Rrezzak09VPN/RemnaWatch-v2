import logging
from datetime import datetime, timezone

from src.database import (
    get_all_inbounds,
    get_all_nodes,
    get_or_create_incident,
    get_setting,
    log_alert,
    update_incident,
)

logger = logging.getLogger(__name__)


class AlertEngine:
    def __init__(self, send_notification_cb=None):
        self._send_notification = send_notification_cb

    async def process(
        self,
        obj_type: str,
        obj_uuid: str,
        incident_type: str,
        is_bad: bool,
        details: str = "",
    ):
        incident = await get_or_create_incident(obj_type, obj_uuid, incident_type)
        fail_threshold = self._fail_threshold(incident_type, int(await get_setting("fail_threshold") or 3))
        recovery_threshold = self._recovery_threshold(incident_type, int(await get_setting("recovery_threshold") or 2))
        cooldown = int(await get_setting("alert_cooldown_seconds") or 3600)

        fails = int(incident["consecutive_fails"] or 0)
        successes = int(incident["consecutive_successes"] or 0)
        is_active = bool(incident["is_active"])
        last_alert_ts = incident.get("last_alert_ts")

        if is_bad:
            fails += 1
            successes = 0
            should_send = False
            now = datetime.now(timezone.utc)

            if fails >= fail_threshold:
                if not is_active:
                    should_send = True
                    is_active = True
                elif self._cooldown_ok(last_alert_ts, cooldown):
                    should_send = True

            if should_send:
                text = await self._bad_text(obj_type, obj_uuid, incident_type, details)
                await self._notify(text)
                await log_alert(obj_type, obj_uuid, incident_type, text, resolved=False)
                last_alert_ts = now.isoformat()

            await update_incident(obj_type, obj_uuid, incident_type, fails, successes, is_active, last_alert_ts)
            return

        successes += 1
        fails = 0
        if is_active and successes >= recovery_threshold:
            is_active = False
            text = await self._recovery_text(obj_type, obj_uuid, incident_type)
            await self._notify(text)
            await log_alert(obj_type, obj_uuid, incident_type, text, resolved=True)
            last_alert_ts = datetime.now(timezone.utc).isoformat()

        await update_incident(obj_type, obj_uuid, incident_type, fails, successes, is_active, last_alert_ts)

    @staticmethod
    def _fail_threshold(incident_type: str, default: int) -> int:
        if incident_type in {"disabled", "traffic_limit"}:
            return 1
        return max(1, default)

    @staticmethod
    def _recovery_threshold(incident_type: str, default: int) -> int:
        if incident_type in {"disabled", "traffic_limit"}:
            return 1
        return max(1, default)

    @staticmethod
    def _cooldown_ok(last_alert_ts, cooldown: int) -> bool:
        if not last_alert_ts:
            return True
        try:
            last = datetime.fromisoformat(str(last_alert_ts).replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - last).total_seconds() >= cooldown
        except Exception:
            return True

    async def _notify(self, text: str):
        if self._send_notification:
            await self._send_notification(text)
        else:
            logger.info("Alert: %s", text)

    def _incident_label(self, incident_type: str) -> str:
        labels = {
            "down": "нода недоступна",
            "disabled": "нода отключена в панели Remnawave",
            "high_memory": "высокое использование RAM",
            "high_load": "высокая нагрузка CPU",
            "high_traffic": "высокий расход трафика",
            "traffic_limit": "достигнут лимит трафика",
            "broken": "inbound не пропускает трафик",
            "wrong_ip": "inbound выходит не через ожидаемый IP",
        }
        return labels.get(incident_type, incident_type)

    async def _bad_text(self, obj_type: str, obj_uuid: str, incident_type: str, details: str) -> str:
        obj_name = await self._get_object_name(obj_type, obj_uuid)
        if incident_type == "disabled":
            text = f"⚪ {obj_name} отключена в панели Remnawave"
        elif incident_type == "down":
            text = f"🔴 {obj_name}: нода недоступна"
        elif incident_type in {"high_memory", "high_load"}:
            text = f"⚠️ {obj_name}: {self._incident_label(incident_type)}"
        elif incident_type in {"high_traffic", "traffic_limit"}:
            text = f"⚠️ {obj_name}: {self._incident_label(incident_type)}"
        elif incident_type == "wrong_ip":
            text = f"⚠️ {obj_name}: выходит не через ожидаемый IP"
        else:
            text = f"🔴 {obj_name}: {self._incident_label(incident_type)}"
        if details:
            text += f"\n{details}"
        return text

    async def _recovery_text(self, obj_type: str, obj_uuid: str, incident_type: str) -> str:
        obj_name = await self._get_object_name(obj_type, obj_uuid)
        if incident_type == "disabled":
            return f"✅ {obj_name} снова включена в панели Remnawave"
        if incident_type == "down":
            return f"✅ {obj_name} снова доступна"
        if incident_type == "wrong_ip":
            return f"✅ {obj_name}: выходной IP снова корректный"
        return f"✅ {obj_name}: восстановлено — {self._incident_label(incident_type)}"

    async def _get_object_name(self, obj_type: str, obj_uuid: str) -> str:
        if obj_type in {"node", "metric", "traffic"}:
            for n in await get_all_nodes():
                if n["uuid"] == obj_uuid:
                    return f"Нода {n['name']}"
        elif obj_type == "inbound":
            for ib in await get_all_inbounds():
                if ib["uuid"] == obj_uuid:
                    return f"Inbound {ib.get('remark') or ib['uuid'][:8]}"
        return f"{obj_type}:{obj_uuid[:8]}"

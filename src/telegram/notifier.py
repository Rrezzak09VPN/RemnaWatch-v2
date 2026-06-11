import logging
from src.config import settings
from src.telegram.bot import get_bot

logger = logging.getLogger(__name__)


async def send_alert_to_admins(text: str):
    bot = get_bot()
    if not bot:
        logger.error("Bot not initialized for alert notification")
        return
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
            logger.info(f"Alert sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send alert to admin {admin_id}: {e}")

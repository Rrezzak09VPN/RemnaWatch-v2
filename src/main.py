import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from src.config import settings
from src.database import init_db, get_new_objects
from src.api.remnawave_api import RemnawaveAPI
from src.alert.engine import AlertEngine
from src.scheduler.manager import init_scheduler, start_scheduler, stop_scheduler
from src.telegram.bot import init_bot, get_bot, get_dp
from src.telegram.notifier import send_alert_to_admins
from src.discovery import run_discovery
from src.telegram.keyboards import main_menu_kb
from src.telegram.middleware import AdminOnlyMiddleware

logger = logging.getLogger(__name__)


async def setup_logging():
    log_path = Path(settings.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_path)),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def onboarding(api: RemnawaveAPI, alert_engine):
    try:
        new_nodes, new_hosts, _, _ = await run_discovery(api)
        total_objects = await get_new_objects()

        nodes = len(new_nodes)
        hosts = len(new_hosts)

        bot = get_bot()
        if bot:
            text = (
                "🎉 <b>RemnaWatch запущен!</b>\n\n"
                f"Обнаружено:\n"
                f"• {nodes} новых нод\n"
                f"• {hosts} новых inbound'ов\n\n"
            )
            if total_objects:
                text += "🆕 Нажмите /setup для выбора объектов мониторинга."
            else:
                text += "✅ Все объекты уже настроены."

            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, text, reply_markup=main_menu_kb())
                except Exception as e:
                    logger.error(f"Failed to send onboarding to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Onboarding failed: {e}")


async def main():
    await setup_logging()
    logger.info("Starting RemnaWatch...")

    if not settings.is_configured():
        logger.error(
            "RemnaWatch not configured! Run install.py first:\n"
            "  python install.py"
        )
        return

    await init_db()
    logger.info("Database initialized")

    api = RemnawaveAPI(settings.remna_api_url, settings.remna_api_token)
    alert_engine = AlertEngine(send_notification_cb=send_alert_to_admins)

    init_scheduler(api, alert_engine)

    bot = init_bot(settings.bot_token)
    dp = get_dp()

    from src.telegram.handlers import (
        start,
        status,
        nodes,
        inbounds,
        metrics,
        traffic,
        intervals,
        thresholds,
        parallel,
        history,
        callbacks,
    )
    dp.message.outer_middleware(AdminOnlyMiddleware())
    dp.callback_query.outer_middleware(AdminOnlyMiddleware())

    dp.include_routers(
        start.router,
        status.router,
        nodes.router,
        inbounds.router,
        metrics.router,
        traffic.router,
        intervals.router,
        thresholds.router,
        parallel.router,
        history.router,
        callbacks.router,
    )

    await onboarding(api, alert_engine)

    await start_scheduler()

    stop_event = asyncio.Event()

    def shutdown():
        logger.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, handle_as_tasks=True)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down...")
        await stop_scheduler()
        await api.close()
        await bot.session.close()
        logger.info("RemnaWatch stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

"""
Telegram bot — runs as a persistent daemon on Hetzner.
Watches Supabase for new notifications and approval requests every 30s.
"""
import logging
from telegram.ext import Application, CallbackQueryHandler
from core.config import TELEGRAM_BOT_TOKEN, RAMI_TELEGRAM_ID
from core.supabase_client import get_supabase
from tgbot.handlers import handle_approval_callback
from tgbot.formatters import format_notification, format_approval_request

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def watch_notifications(context):
    """Send unread critical/warning notifications to Rami."""
    try:
        supabase = get_supabase()
        result = (
            supabase.table("notifications")
            .select("*")
            .eq("status", "unread")
            .in_("severity", ["critical", "warning"])
            .order("created_at", desc=False)
            .limit(10)
            .execute()
        )
        for notif in result.data:
            await context.bot.send_message(
                chat_id=RAMI_TELEGRAM_ID,
                text=format_notification(notif),
                parse_mode="HTML",
            )
            supabase.table("notifications").update(
                {"status": "read"}
            ).eq("id", notif["id"]).execute()
    except Exception as e:
        logger.error(f"watch_notifications error: {e}")


async def watch_approvals(context):
    """Send pending approval requests that haven't been sent to Telegram yet."""
    try:
        supabase = get_supabase()
        result = (
            supabase.table("approval_requests")
            .select("*")
            .eq("status", "pending")
            .is_("telegram_msg_id", "null")
            .order("requested_at", desc=False)
            .limit(10)
            .execute()
        )
        for req in result.data:
            text, keyboard = format_approval_request(req)
            msg = await context.bot.send_message(
                chat_id=RAMI_TELEGRAM_ID,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            supabase.table("approval_requests").update(
                {"telegram_msg_id": str(msg.message_id)}
            ).eq("id", req["id"]).execute()
    except Exception as e:
        logger.error(f"watch_approvals error: {e}")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(
        handle_approval_callback,
        pattern=r"^(approve|reject):",
    ))

    app.job_queue.run_repeating(watch_notifications, interval=30, first=10)
    app.job_queue.run_repeating(watch_approvals, interval=30, first=20)

    logger.info("Bot started. Polling for updates...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

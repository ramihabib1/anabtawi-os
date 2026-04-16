import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, approval_id = query.data.split(":", 1)
    new_status = "approved" if action == "approve" else "rejected"

    try:
        supabase = get_supabase()
        supabase.table("approval_requests").update({
            "status": new_status,
            "responded_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", approval_id).execute()

        emoji = "✅" if new_status == "approved" else "❌"
        original = query.message.text or ""
        await query.edit_message_text(
            text=f"{original}\n\n{emoji} <b>{new_status.upper()}</b> by {query.from_user.first_name}",
            parse_mode="HTML",
            reply_markup=None,
        )
        logger.info(f"Approval {approval_id[:8]} → {new_status}")
    except Exception as e:
        logger.error(f"Failed to process approval callback: {e}")
        await query.edit_message_text(
            text=f"❗ Error processing response: {e}",
            reply_markup=None,
        )

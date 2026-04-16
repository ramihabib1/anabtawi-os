from datetime import datetime, timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

ACTION_LABELS = {
    "fba_replenishment": "FBA Restock",
    "price_change": "Price Change",
    "ppc_bid_change": "PPC Bid Change",
    "ppc_budget_change": "PPC Budget Change",
    "listing_change": "Listing Update",
}


def format_notification(notif: dict) -> str:
    emoji = SEVERITY_EMOJI.get(notif["severity"], "⚪")
    return f"{emoji} <b>{notif['title']}</b>\n{notif['body']}"


def format_approval_request(req: dict) -> tuple[str, InlineKeyboardMarkup]:
    payload = req.get("payload", {})
    action_label = ACTION_LABELS.get(req["action_type"], req["action_type"])

    lines = [
        "🔔 <b>APPROVAL REQUIRED</b>",
        "",
        f"<b>Agent:</b> {req['agent']}",
        f"<b>Action:</b> {action_label}",
        "",
        req["description"],
    ]

    reasoning = payload.get("reasoning")
    if reasoning:
        lines += ["", f"<b>Reasoning:</b> {reasoning}"]

    expires_at = req.get("expires_at", "")
    if expires_at:
        try:
            dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            lines += ["", f"<b>Expires:</b> {dt.strftime('%b %d, %I:%M %p UTC')}"]
        except Exception:
            pass

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{req['id']}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject:{req['id']}"),
    ]])

    return "\n".join(lines), keyboard

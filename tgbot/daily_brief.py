"""
Daily brief compiler — called by cron at 07:00 UTC.
Pulls today's data from Supabase and sends a morning summary to Rami.

Usage: python3 -m tgbot.daily_brief
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from telegram import Bot
from core.config import TELEGRAM_BOT_TOKEN, RAMI_TELEGRAM_ID
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def compile_brief() -> str:
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = (today - timedelta(days=1)).isoformat()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Notifications from last 24h
    notifs = (
        supabase.table("notifications")
        .select("severity, title, body")
        .in_("severity", ["critical", "warning"])
        .gte("created_at", day_start)
        .order("severity")
        .execute()
        .data
    )

    # Pending approvals count
    pending_count = len(
        supabase.table("approval_requests")
        .select("id")
        .eq("status", "pending")
        .execute()
        .data
    )

    # Yesterday's sales totals
    sales = (
        supabase.table("sales_daily")
        .select("units_sold, revenue")
        .eq("sale_date", yesterday)
        .execute()
        .data
    )

    # Today's agent runs
    runs = (
        supabase.table("agent_runs")
        .select("agent, success, duration_ms, output_summary")
        .gte("started_at", day_start)
        .execute()
        .data
    )

    lines = [f"📊 <b>Habib Distribution — {today.strftime('%B %d, %Y')}</b>"]

    # Alerts
    critical = [n for n in notifs if n["severity"] == "critical"]
    warnings = [n for n in notifs if n["severity"] == "warning"]

    if critical:
        lines.append("\n🔴 <b>CRITICAL</b>")
        for n in critical:
            lines.append(f"• <b>{n['title']}</b>: {n['body']}")

    if warnings:
        lines.append("\n🟡 <b>ATTENTION</b>")
        for n in warnings:
            lines.append(f"• <b>{n['title']}</b>: {n['body']}")

    if not critical and not warnings:
        lines.append("\n🟢 <b>ALL CLEAR</b> — No critical or warning alerts")

    # Yesterday's numbers
    total_units = sum(r.get("units_sold") or 0 for r in sales)
    total_revenue = sum(float(r.get("revenue") or 0) for r in sales)
    lines.append(f"\n📈 <b>YESTERDAY</b>")
    lines.append(f"Revenue: ${total_revenue:,.2f} CAD | Units sold: {total_units}")

    # Agent run summary
    if runs:
        success_count = sum(1 for r in runs if r["success"])
        lines.append(f"\n🤖 <b>AGENTS</b> ({success_count}/{len(runs)} successful)")
        for r in runs:
            icon = "✅" if r["success"] else "❌"
            lines.append(f"  {icon} {r['agent']}")

    # Pending approvals
    if pending_count:
        lines.append(f"\n⏳ <b>PENDING</b>")
        lines.append(f"{pending_count} approval(s) awaiting your response")

    return "\n".join(lines)


async def send_daily_brief():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    text = compile_brief()
    await bot.send_message(
        chat_id=RAMI_TELEGRAM_ID,
        text=text,
        parse_mode="HTML",
    )
    logger.info("Daily brief sent.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(send_daily_brief())

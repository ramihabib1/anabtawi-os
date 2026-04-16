"""
Verify the outcome of an E2E approval test.

Usage:
  python3 scripts/verify_approval.py <approval_id>

Prints the current status, responded_at, and execution_result for the row.
"""
import sys
from core.supabase_client import get_supabase


def verify(approval_id: str):
    supabase = get_supabase()
    result = supabase.table("approval_requests").select(
        "id, status, responded_at, execution_result, telegram_msg_id"
    ).eq("id", approval_id).execute()

    if not result.data:
        print(f"❌ Row {approval_id[:8]} not found")
        sys.exit(1)

    row = result.data[0]
    status = row["status"]
    emoji = {
        "pending": "⏳",
        "approved": "✅",
        "rejected": "❌",
        "expired": "🕐",
        "auto_approved": "🤖",
    }.get(status, "❓")

    print(f"\n{emoji} Status: {status.upper()}")
    print(f"   ID:           {row['id']}")
    print(f"   Telegram msg: {row.get('telegram_msg_id', 'not sent yet')}")
    print(f"   Responded at: {row.get('responded_at', 'not yet')}")
    print(f"   Exec result:  {row.get('execution_result', 'not executed yet')}")

    if status == "approved":
        print()
        print("✅ Approval flow working. Executor will pick this up on its next 60s poll.")
        print("   Check audit_log after ~90s to confirm execution_result was written.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/verify_approval.py <approval_id>")
        sys.exit(1)
    verify(sys.argv[1])

"""
Telegram E2E test helper.

Inserts a dummy fba_replenishment approval_requests row with status='pending'
and no telegram_msg_id, so the bot will pick it up within 30 seconds and send
an approval message to Rami's phone.

Usage:
  1. Run the bot in one terminal:  python3 -m tgbot.bot
  2. Run this script in another:   python3 scripts/test_approval.py
  3. Wait ≤30s — approval message should appear on phone
  4. Tap ✅ Approve
  5. Verify the flip:              python3 scripts/verify_approval.py <id>
  6. Clean up:                     python3 scripts/test_approval.py --cleanup <id>
"""
import sys
from datetime import datetime, timezone, timedelta
from core.supabase_client import get_supabase


def insert_test_row() -> str:
    supabase = get_supabase()
    result = supabase.table("approval_requests").insert({
        "action_type": "fba_replenishment",
        "agent": "inventory_agent",
        "description": (
            "TEST ROW — SKU-017 Baklava: send 50 units to FBA.\n"
            "Delete this row after the E2E test is confirmed."
        ),
        "payload": {
            "sku": "SKU-017-TEST",
            "units_to_send": 50,
            "boxes_to_send": 2,
            "reasoning": "E2E test of the Telegram approval flow.",
        },
        "status": "pending",
        "expires_at": (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat(),
    }).execute()

    row = result.data[0]
    approval_id = row["id"]

    print(f"\n✅ Test row created")
    print(f"   ID: {approval_id}")
    print()
    print("Next steps:")
    print("  1. Check your phone — approval message should arrive within 30s")
    print("  2. Tap ✅ Approve")
    print(f"  3. Verify: python3 scripts/verify_approval.py {approval_id}")
    print(f"  4. Cleanup: python3 scripts/test_approval.py --cleanup {approval_id}")

    return approval_id


def cleanup(approval_id: str):
    supabase = get_supabase()
    result = supabase.table("approval_requests").delete().eq("id", approval_id).execute()
    if result.data:
        print(f"🗑  Deleted test row {approval_id[:8]}")
    else:
        print(f"Row {approval_id[:8]} not found (already deleted?)")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--cleanup":
        cleanup(sys.argv[2])
    elif len(sys.argv) == 1:
        insert_test_row()
    else:
        print("Usage:")
        print("  python3 scripts/test_approval.py")
        print("  python3 scripts/test_approval.py --cleanup <id>")
        sys.exit(1)

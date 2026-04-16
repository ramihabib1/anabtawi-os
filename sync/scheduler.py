"""
Sync scheduler daemon — runs all SP-API sync jobs on a schedule.

Schedule:
  :00 every hour    — inventory_sync
  :15 every hour    — orders_sync
  :30 every hour    — expire_approvals
  04:30 daily       — listings_sync (run before agents at 05:30)
  06:00 daily       — listings_sync (second run — catches mid-day changes)
  05:00 daily       — fees_sync
  05:10 daily       — ppc_sync
  08:00 daily       — reviews_sync
  Monday 09:00      — competitor_sync

Run as a daemon: python -m sync.scheduler
Or via systemd/cron on Hetzner.

Alternative: skip this daemon and use cron directly:
  0 * * * *   python -m sync.jobs.inventory_sync
  15 * * * *  python -m sync.jobs.orders_sync
  30 * * * *  python -m sync.jobs.expire_approvals
  30 4 * * *  python -m sync.jobs.listings_sync
  0 5 * * *   python -m sync.jobs.fees_sync
  10 5 * * *  python -m sync.jobs.ppc_sync
  0 8 * * *   python -m sync.jobs.reviews_sync
  0 9 * * 1   python -m sync.jobs.competitor_sync
"""

from __future__ import annotations

import asyncio
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

import schedule

from sync.utils.logging import configure_logging, get_logger
from sync.utils.telegram import send_to_role

configure_logging()
logger = get_logger(__name__)


async def _run_job(name: str, coro_fn: Callable[[], Awaitable[Any]]) -> None:
    """Execute a job coroutine, log result, alert on failure."""
    logger.info("job_start", job=name)
    try:
        result = await coro_fn()
        logger.info("job_done", job=name, result=result)
    except Exception:
        tb = traceback.format_exc()
        logger.error("job_failed", job=name, traceback=tb)
        try:
            await send_to_role(
                "rami",
                f"❌ *Sync job failed:* `{name}`\n\n```\n{tb[-800:]}\n```",
            )
        except Exception:
            pass


def _schedule_async(name: str, coro_fn: Callable[[], Awaitable[Any]]) -> None:
    """Wrap async job so the schedule library can call it synchronously."""
    asyncio.create_task(_run_job(name, coro_fn))


def _register_jobs() -> None:
    from sync.jobs import (
        competitor_sync,
        expire_approvals,
        fees_sync,
        inventory_sync,
        listings_sync,
        orders_sync,
        ppc_sync,
        reviews_sync,
    )

    # ── Hourly ────────────────────────────────────────────────────────────────
    schedule.every().hour.at(":00").do(
        _schedule_async, "inventory_sync", inventory_sync.run
    )
    schedule.every().hour.at(":15").do(
        _schedule_async, "orders_sync", orders_sync.run
    )
    schedule.every().hour.at(":30").do(
        _schedule_async, "expire_approvals", expire_approvals.run
    )

    # ── Daily — listings_sync runs twice: 04:30 (before agents) + 06:00 ─────
    schedule.every().day.at("04:30").do(
        _schedule_async, "listings_sync_morning", listings_sync.run
    )
    schedule.every().day.at("06:00").do(
        _schedule_async, "listings_sync_midday", listings_sync.run
    )
    schedule.every().day.at("05:00").do(
        _schedule_async, "fees_sync", fees_sync.run
    )
    schedule.every().day.at("05:10").do(
        _schedule_async, "ppc_sync", ppc_sync.run
    )
    schedule.every().day.at("08:00").do(
        _schedule_async, "reviews_sync", reviews_sync.run
    )

    # ── Weekly ────────────────────────────────────────────────────────────────
    schedule.every().monday.at("09:00").do(
        _schedule_async, "competitor_sync", competitor_sync.run
    )

    logger.info("jobs_registered", count=len(schedule.jobs))


async def _scheduler_loop() -> None:
    """Run the schedule check loop every 30 seconds."""
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)


async def main() -> None:
    logger.info("sync_scheduler_starting")
    _register_jobs()
    await _scheduler_loop()


if __name__ == "__main__":
    asyncio.run(main())

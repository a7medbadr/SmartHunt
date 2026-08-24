from apscheduler.schedulers.asyncio import AsyncIOScheduler

# misfire_grace_time=None ("no limit") — a trigger fire that the event
# loop can't reach in time is deferred and run whenever the loop is next
# free, instead of being silently dropped past APScheduler's own tight
# 1-second default grace window. Found 2026-08-13 as the real cause of
# scan_linkedin_home_feed_hourly (and, by the same mechanism, every other
# interval/cron job here) going 3-11h between runs with zero container
# restarts to blame — CLAUDE.md already documents the event loop being
# pinned for 80+ minutes at a time by Chromium/AI CPU contention, which
# blows past a 1-second grace window trivially. coalesce=True (already
# the library default) keeps multiple missed fires from piling up into a
# burst once the loop is free again.
scheduler = AsyncIOScheduler(job_defaults={"misfire_grace_time": None, "coalesce": True})

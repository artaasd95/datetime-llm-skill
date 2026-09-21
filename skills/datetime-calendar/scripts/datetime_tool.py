#!/usr/bin/env python3
"""
Deterministic datetime/calendar utility for LLM agents.

No third-party dependencies.
Python 3.9+ recommended; Python 3.11+ preferred.
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


WEEKDAY_SHORT = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({
        "ok": False,
        "error": message,
    }, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def get_zone(name: str | None) -> ZoneInfo:
    if not name:
        # System local timezone. Python normally gets this from the host OS.
        local_name = os.environ.get("TZ")
        if local_name:
            try:
                return ZoneInfo(local_name)
            except ZoneInfoNotFoundError:
                pass

        # datetime.now().astimezone() obtains the system local tz.
        local_tz = datetime.now().astimezone().tzinfo
        if local_tz is None:
            return ZoneInfo("UTC")

        # ZoneInfo is preferable because it preserves the IANA rules.
        key = getattr(local_tz, "key", None)
        if key:
            try:
                return ZoneInfo(key)
            except ZoneInfoNotFoundError:
                pass

        # Fixed-offset fallback if the OS exposes no IANA zone name.
        return local_tz  # type: ignore[return-value]

    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        fail(
            f"Unknown timezone '{name}'. Use an IANA timezone such as "
            f"Europe/Berlin, Europe/Amsterdam, Asia/Tokyo, or UTC."
        )


def offset_string(dt: datetime) -> str:
    return dt.strftime("%z")[:-2] + ":" + dt.strftime("%z")[-2:]


def iso_weekday_index(dt: datetime) -> int:
    return dt.weekday()  # Monday=0 ... Sunday=6


def now_command(tz_name: str | None) -> dict:
    tz = get_zone(tz_name)
    current = datetime.now(tz)

    return {
        "ok": True,
        "operation": "now",
        "timezone": getattr(tz, "key", tz_name or "system-local"),
        "utc": current.astimezone(timezone.utc).isoformat(),
        "local": current.isoformat(),
        "date": current.date().isoformat(),
        "time": current.strftime("%H:%M:%S"),
        "weekday": current.strftime("%A"),
        "weekday_short": WEEKDAY_SHORT[current.weekday()],
        "weekday_index": current.weekday(),
        "utc_offset": offset_string(current),
        "timestamp_epoch": current.timestamp(),
        "is_dst": bool(current.dst()),
    }


def parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        fail(
            f"Invalid ISO-8601 datetime '{value}'. "
            "Example: 2026-09-21T21:37:00+03:30"
        )
        raise exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        fail(
            "Timezone-naive datetime rejected. Include an explicit offset, "
            "for example 2026-09-21T21:37:00+03:30."
        )

    return dt


def convert_command(value: str, target_name: str) -> dict:
    source = parse_datetime(value)
    target_tz = get_zone(target_name)
    target = source.astimezone(target_tz)

    source_offset = source.utcoffset().total_seconds() / 3600
    target_offset = target.utcoffset().total_seconds() / 3600

    return {
        "ok": True,
        "operation": "convert",
        "source": source.isoformat(),
        "target": target.isoformat(),
        "source_timezone": str(source.tzinfo),
        "target_timezone": getattr(target_tz, "key", target_name),
        "source_local": source.isoformat(),
        "target_local": target.isoformat(),
        "target_date": target.date().isoformat(),
        "target_time": target.strftime("%H:%M:%S"),
        "target_weekday": target.strftime("%A"),
        "target_weekday_short": WEEKDAY_SHORT[target.weekday()],
        "target_utc_offset": offset_string(target),
        "offset_change_hours": target_offset - source_offset,
        "is_dst": bool(target.dst()),
    }


def day_record(year: int, month: int, day: int) -> dict:
    d = datetime(year, month, day)
    return {
        "date": d.date().isoformat(),
        "day": day,
        "weekday": d.strftime("%A"),
        "weekday_short": WEEKDAY_SHORT[d.weekday()],
        "weekday_index": d.weekday(),
        "week_of_year": d.isocalendar().week,
        "iso_week": f"{d.isocalendar().year}-W{d.isocalendar().week:02d}",
        "is_weekend": d.weekday() >= 5,
        "is_first_of_month": day == 1,
        "is_last_of_month": day == calendar.monthrange(year, month)[1],
    }


def month_command(year: int, month: int) -> dict:
    if not 1 <= month <= 12:
        fail("Month must be between 1 and 12.")
    if year < 1 or year > 9999:
        fail("Year must be between 1 and 9999.")

    days_in_month = calendar.monthrange(year, month)[1]
    first = datetime(year, month, 1)
    last = datetime(year, month, days_in_month)

    days = [day_record(year, month, d) for d in range(1, days_in_month + 1)]

    # Monday-first calendar grid. `None` represents an outside-month cell.
    matrix = calendar.monthcalendar(year, month)
    weeks = []
    for week_index, row in enumerate(matrix, start=1):
        weeks.append({
            "week_in_month": week_index,
            "monday": row[0] or None,
            "tuesday": row[1] or None,
            "wednesday": row[2] or None,
            "thursday": row[3] or None,
            "friday": row[4] or None,
            "saturday": row[5] or None,
            "sunday": row[6] or None,
        })

    llm_lines = [
        f"{calendar.month_name[month]} {year} | {days_in_month} days"
    ]
    llm_lines.extend(
        f"{d['day']:02d} | {d['weekday_short']} | {d['date']}"
        for d in days
    )

    return {
        "ok": True,
        "operation": "month",
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "month_key": f"{year:04d}-{month:02d}",
        "days_in_month": days_in_month,
        "first_date": first.date().isoformat(),
        "last_date": last.date().isoformat(),
        "first_weekday": first.strftime("%A"),
        "first_weekday_short": WEEKDAY_SHORT[first.weekday()],
        "last_weekday": last.strftime("%A"),
        "last_weekday_short": WEEKDAY_SHORT[last.weekday()],
        "first_iso_week": f"{first.isocalendar().year}-W{first.isocalendar().week:02d}",
        "last_iso_week": f"{last.isocalendar().year}-W{last.isocalendar().week:02d}",
        "days": days,
        "weeks": weeks,
        "llm_lines": llm_lines,
    }


def parse_month(value: str) -> tuple[int, int]:
    try:
        year_s, month_s = value.split("-", 1)
        return int(year_s), int(month_s)
    except (ValueError, AttributeError):
        fail("Month must use YYYY-MM format, for example 2026-09.")
        raise AssertionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Datetime, timezone conversion, and calendar utility."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    now = sub.add_parser("now", help="Get the current system datetime.")
    now.add_argument("--timezone", help="IANA timezone, e.g. Europe/Berlin.")

    convert = sub.add_parser("convert", help="Convert an aware datetime.")
    convert.add_argument("--datetime", required=True, dest="datetime_value")
    convert.add_argument("--to-timezone", required=True)

    month = sub.add_parser("month", help="Build a complete month calendar.")
    group = month.add_mutually_exclusive_group(required=True)
    group.add_argument("--month", help="Month as YYYY-MM.")
    group.add_argument("--year", type=int)
    month.add_argument("--month-number", type=int, dest="month_number")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "now":
        result = now_command(args.timezone)

    elif args.command == "convert":
        result = convert_command(args.datetime_value, args.to_timezone)

    elif args.command == "month":
        if args.month:
            year, month = parse_month(args.month)
        else:
            if args.month_number is None:
                fail("When using --year, also provide --month-number.")
            year, month = args.year, args.month_number
        result = month_command(year, month)

    else:
        parser.error("Unknown command.")
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

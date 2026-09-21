---
name: datetime-calendar
description: Provides deterministic current date/time, timezone conversion, and complete month-calendar generation. Use whenever the user or agent needs the current date or time, a timezone-specific time, datetime conversion, weekday information, month boundaries, number of days in a month, or a complete structured calendar.
---

# Datetime & Calendar

Use the bundled Python utility whenever a current datetime or calendar calculation is required. Do not infer the current datetime from conversation metadata or calculate month lengths manually.

## Utility

The utility is at:

```text
${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py
```

Run it with Python:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py" now
```

## Operations

### 1. Current datetime

For the current system-local datetime:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py" now
```

For a named IANA timezone:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py" now --timezone Europe/Berlin
```

The result is JSON containing the local datetime, UTC datetime, date, time, weekday, UTC offset, epoch timestamp, and DST state.

### 2. Timezone conversion

Input must be timezone-aware ISO-8601:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py" convert --datetime "2026-09-21T21:37:00+03:30" --to-timezone Europe/Berlin
```

Never silently assume UTC for a timezone-naive input. The utility rejects timezone-naive datetimes.

Use IANA timezone names such as:

- `UTC`
- `Europe/Berlin`
- `Europe/Amsterdam`
- `Asia/Tehran`
- `Asia/Tokyo`
- `America/New_York`
- `America/Los_Angeles`

### 3. Complete month calendar

For a specific month:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/datetime-calendar/scripts/datetime_tool.py" month --month 2026-09
```

The output contains:

- `month_name`
- `year`
- `month`
- `month_key`
- `days_in_month`
- `first_date`
- `last_date`
- first/last weekday
- first/last ISO week
- `days`: every individual date
- `weeks`: Monday-first calendar grid
- `llm_lines`: compact LLM-friendly representation

Each item in `days` includes:

```json
{
  "date": "2026-09-01",
  "day": 1,
  "weekday": "Tuesday",
  "weekday_short": "Tu",
  "weekday_index": 1,
  "week_of_year": 36,
  "iso_week": "2026-W36",
  "is_weekend": false,
  "is_first_of_month": true,
  "is_last_of_month": false
}
```

`weekday_index` uses Monday=0 through Sunday=6 (matching Python's `datetime.weekday()`).

The compact representation looks like:

```text
September 2026 | 30 days
01 | Tu | 2026-09-01
02 | We | 2026-09-02
03 | Th | 2026-09-03
...
30 | We | 2026-09-30
```

## Relative-date workflow

For requests such as "this month", "next month", "today", or "tomorrow":

1. Run `now`.
2. Use the returned date/time as the authoritative current point.
3. Determine the requested date/month from that result.
4. Run `month` when a complete month is required.
5. Do not guess or use the conversation timestamp.

## Output principles

Prefer the JSON fields for reasoning and structured operations.

Use `llm_lines` when injecting a complete calendar into context or when the user asks for a simple structured list.

Use the `weeks` field when a visual Monday-first calendar grid is useful.

Always preserve ISO-8601 dates (`YYYY-MM-DD`) internally.

## Correctness rules

- Never hard-code month lengths.
- Never infer today's date.
- Never silently assign a timezone to a naive datetime.
- Use IANA timezone identifiers for named zones.
- Let Python `zoneinfo` handle DST.
- Treat the script output as authoritative for calculations.

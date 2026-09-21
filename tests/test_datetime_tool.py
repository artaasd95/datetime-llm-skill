import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "datetime-calendar" / "scripts" / "datetime_tool.py"


def run(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return result


def test_month_september_2026():
    result = run("month", "--month", "2026-09")
    assert result.returncode == 0
    data = json.loads(result.stdout)

    assert data["month_name"] == "September"
    assert data["days_in_month"] == 30
    assert data["first_date"] == "2026-09-01"
    assert data["last_date"] == "2026-09-30"
    assert data["days"][0]["weekday_short"] == "Tu"
    assert data["days"][-1]["weekday_short"] == "We"
    assert len(data["days"]) == 30


def test_february_leap_year():
    result = run("month", "--month", "2028-02")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["days_in_month"] == 29


def test_february_non_leap_year():
    result = run("month", "--month", "2027-02")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["days_in_month"] == 28


def test_timezone_conversion():
    result = run(
        "convert",
        "--datetime",
        "2026-09-21T21:37:00+03:30",
        "--to-timezone",
        "Europe/Berlin",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)

    assert data["target_date"] == "2026-09-21"
    assert data["target_time"] == "20:07:00"
    assert data["target_weekday"] == "Monday"


def test_naive_datetime_is_rejected():
    result = run(
        "convert",
        "--datetime",
        "2026-09-21T21:37:00",
        "--to-timezone",
        "UTC",
    )
    assert result.returncode != 0
    assert "Timezone-naive" in result.stderr


def test_now():
    result = run("now", "--timezone", "UTC")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["operation"] == "now"
    assert data["timezone"] == "UTC"
    assert data["utc"].endswith("+00:00")

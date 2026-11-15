"""Parse calendar dates in mapped fields. Numeric local dates use day first."""
from datetime import datetime, time
import re


def calendar_date(value):
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    parts = re.fullmatch(r"(.+?)(?:[ T](\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?))?", text)
    if parts:
        day, clock = parts.groups()
        if clock:
            time.fromisoformat(clock.zfill(5))
        normalized = re.sub(r"[/.,\s-]+", "-", day.strip()).strip("-")
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y", "%d-%B-%Y", "%b-%d-%Y", "%B-%d-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Invalid date {text!r}. Use DD/MM/YYYY or YYYY-MM-DD.")

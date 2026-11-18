from datetime import datetime

from app.models.event import CATEGORIES


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def validate_event_data(data):
    """Return (cleaned_data, None) if valid, or (None, error_message)."""
    if not isinstance(data, dict):
        return None, "Invalid request data"

    cleaned = {}

    for field in ("title", "description", "venue", "category"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"{field} is required"
        cleaned[field] = value.strip()

    if len(cleaned["title"]) > 200:
        return None, "title must be at most 200 characters"

    if len(cleaned["venue"]) > 200:
        return None, "venue must be at most 200 characters"

    if cleaned["category"] not in CATEGORIES:
        return None, "category must be one of: " + ", ".join(CATEGORIES)

    try:
        cleaned["event_date"] = _parse_date(data.get("event_date"))
    except (TypeError, ValueError):
        return None, "event_date must be in YYYY-MM-DD format"

    try:
        cleaned["start_time"] = _parse_time(data.get("start_time"))
        cleaned["end_time"] = _parse_time(data.get("end_time"))
    except (TypeError, ValueError):
        return None, "start_time and end_time must be in HH:MM format"

    if cleaned["end_time"] <= cleaned["start_time"]:
        return None, "end_time must be after start_time"

    capacity = data.get("capacity")
    if (
        not isinstance(capacity, int)
        or isinstance(capacity, bool)
        or capacity < 1
    ):
        return None, "capacity must be a whole number of at least 1"
    cleaned["capacity"] = capacity

    image_url = data.get("image_url")
    if image_url in (None, ""):
        cleaned["image_url"] = None
    else:
        if (
            not isinstance(image_url, str)
            or len(image_url) > 500
            or not image_url.startswith(("http://", "https://"))
        ):
            return None, "image_url must be an http or https URL"
        cleaned["image_url"] = image_url

    return cleaned, None
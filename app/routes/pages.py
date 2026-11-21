from datetime import date, datetime

from flask import Blueprint, render_template

from app.extensions import db
from app.models.event import CATEGORIES, Event

pages_bp = Blueprint("pages", __name__)

CATEGORY_ICONS = {
    "Technical": "bi-cpu",
    "Cultural": "bi-music-note-beamed",
    "Sports": "bi-trophy",
    "Workshops": "bi-tools",
    "Seminars": "bi-mic",
    "Other": "bi-stars",
}


@pages_bp.app_template_filter("pretty_date")
def pretty_date(value):
    """Turn '2026-12-05' into '05 Dec 2026'."""
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")


@pages_bp.route("/")
def index():
    upcoming = db.session.execute(
        db.select(Event)
        .where(Event.event_date >= date.today())
        .order_by(Event.event_date, Event.start_time)
        .limit(6)
    ).scalars().all()

    return render_template(
        "index.html",
        events=[event.to_dict() for event in upcoming],
        categories=[(name, CATEGORY_ICONS[name]) for name in CATEGORIES],
    )
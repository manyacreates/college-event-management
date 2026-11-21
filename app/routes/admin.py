from datetime import datetime

from flask import Blueprint, jsonify
from sqlalchemy import func

from app.decorators import admin_required
from app.extensions import db
from app.models.event import Event
from app.models.feedback import Feedback
from app.models.registration import STATUS_REGISTERED, Registration
from app.models.user import User

admin_bp = Blueprint("admin", __name__)

POPULAR_LIMIT = 5


@admin_bp.route("/api/admin/ping", methods=["GET"])
@admin_required
def ping():
    return jsonify({"success": True, "message": "pong"}), 200


@admin_bp.route("/api/admin/stats", methods=["GET"])
@admin_required
def stats():
    now = datetime.now()

    total_users = db.session.scalar(
        db.select(func.count(User.id)).where(User.role == "student")
    )

    total_registrations = db.session.scalar(
        db.select(func.count(Registration.id)).where(
            Registration.status == STATUS_REGISTERED
        )
    )

    # An event is completed once its end time has passed.
    events = db.session.execute(
        db.select(Event.event_date, Event.end_time)
    ).all()
    completed = sum(
        1 for event_date, end_time in events
        if datetime.combine(event_date, end_time) < now
    )

    average = db.session.scalar(db.select(func.avg(Feedback.rating)))

    # Outer join so events with zero registrations still count as 0.
    registered_count = func.count(Registration.id)
    popular_rows = db.session.execute(
        db.select(Event.id, Event.title, registered_count)
        .outerjoin(
            Registration,
            (Registration.event_id == Event.id)
            & (Registration.status == STATUS_REGISTERED),
        )
        .group_by(Event.id)
        .order_by(registered_count.desc(), Event.id)
        .limit(POPULAR_LIMIT)
    ).all()

    return jsonify({
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_events": len(events),
            "upcoming_events": len(events) - completed,
            "completed_events": completed,
            "total_registrations": total_registrations,
            "average_rating": round(float(average), 2) if average is not None else None,
            "popular_events": [
                {"id": event_id, "title": title, "registrations": count}
                for event_id, title, count in popular_rows
            ],
        },
    }), 200
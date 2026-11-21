from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import or_
from app.models.notification import Notification
from app.services.notifications import notify_registered_students
from app.decorators import admin_required
from app.extensions import db
from app.models.event import Event
from app.validators import validate_event_data

events_bp = Blueprint("events", __name__)


def _error(message, status):
    return jsonify({"success": False, "message": message}), status


def _get_event_or_none(event_id):
    return db.session.get(Event, event_id)


@events_bp.route("/api/events", methods=["GET"])
def list_events():
    query = db.select(Event)

    search = request.args.get("q", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Event.title.ilike(pattern), Event.description.ilike(pattern))
        )

    category = request.args.get("category", "").strip()
    if category:
        query = query.where(Event.category == category)

    query = query.order_by(Event.event_date, Event.start_time)
    events = db.session.execute(query).scalars().all()

    return jsonify({
        "success": True,
        "events": [event.to_dict() for event in events],
    }), 200


@events_bp.route("/api/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = _get_event_or_none(event_id)
    if event is None:
        return _error("Event not found", 404)

    return jsonify({"success": True, "event": event.to_dict()}), 200


@events_bp.route("/api/events", methods=["POST"])
@admin_required
def create_event():
    cleaned, error = validate_event_data(request.get_json(silent=True))
    if error:
        return _error(error, 400)

    event = Event(**cleaned, organizer_id=current_user.id)
    db.session.add(event)
    db.session.commit()

    return jsonify({"success": True, "event": event.to_dict()}), 201


@events_bp.route("/api/events/<int:event_id>", methods=["PUT"])
@admin_required
def update_event(event_id):
    event = _get_event_or_none(event_id)
    if event is None:
        return _error("Event not found", 404)

    cleaned, error = validate_event_data(request.get_json(silent=True))
    if error:
        return _error(error, 400)

    for field, value in cleaned.items():
        setattr(event, field, value)
    notify_registered_students(
        event, f"Details for {event.title} have been updated."
    )
    db.session.commit()

    return jsonify({"success": True, "event": event.to_dict()}), 200

@events_bp.route("/api/events/<int:event_id>", methods=["DELETE"])
@admin_required
def delete_event(event_id):
    event = _get_event_or_none(event_id)
    if event is None:
        return _error("Event not found", 404)

    db.session.execute(
        db.update(Notification)
        .where(Notification.event_id == event.id)
        .values(event_id=None)
    )
    db.session.delete(event)
    db.session.commit()

    return jsonify({"success": True, "message": "Event deleted"}), 200
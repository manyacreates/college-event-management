from datetime import datetime

from flask import Blueprint, jsonify
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.decorators import admin_required, student_required
from app.extensions import db
from app.models.event import Event
from app.models.registration import (
    STATUS_CANCELLED,
    STATUS_REGISTERED,
    Registration,
    count_active,
)
from app.models.user import User

registrations_bp = Blueprint("registrations", __name__)


def _error(message, status):
    return jsonify({"success": False, "message": message}), status


def _get_event_locked(event_id):
    """Fetch the event and lock its row until commit (see notes below)."""
    return db.session.execute(
        db.select(Event).where(Event.id == event_id).with_for_update()
    ).scalar_one_or_none()


def _find_registration(user_id, event_id):
    return db.session.execute(
        db.select(Registration).filter_by(user_id=user_id, event_id=event_id)
    ).scalar_one_or_none()


@registrations_bp.route("/api/events/<int:event_id>/register", methods=["POST"])
@student_required
def register_for_event(event_id):
    event = _get_event_locked(event_id)
    if event is None:
        return _error("Event not found", 404)

    starts_at = datetime.combine(event.event_date, event.start_time)
    if starts_at < datetime.now():
        return _error("Registration is closed for past events", 400)

    registration = _find_registration(current_user.id, event_id)
    if registration and registration.status == STATUS_REGISTERED:
        return _error("You are already registered for this event", 409)

    if count_active(event_id) >= event.capacity:
        return _error("This event is full", 409)

    if registration:
        registration.status = STATUS_REGISTERED
        registration.registration_date = datetime.now().astimezone()
    else:
        registration = Registration(
            user_id=current_user.id, event_id=event_id, status=STATUS_REGISTERED
        )
        db.session.add(registration)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("You are already registered for this event", 409)

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "registration": registration.to_dict(),
    }), 201


@registrations_bp.route("/api/events/<int:event_id>/register", methods=["DELETE"])
@student_required
def cancel_registration(event_id):
    registration = _find_registration(current_user.id, event_id)
    if registration is None or registration.status != STATUS_REGISTERED:
        return _error("You are not registered for this event", 404)

    registration.status = STATUS_CANCELLED
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration cancelled",
    }), 200


@registrations_bp.route("/api/registrations/me", methods=["GET"])
@student_required
def my_registrations():
    registrations = db.session.execute(
        db.select(Registration)
        .where(Registration.user_id == current_user.id)
        .order_by(Registration.registration_date.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "registrations": [r.to_dict(include_event=True) for r in registrations],
    }), 200


@registrations_bp.route("/api/events/<int:event_id>/participants", methods=["GET"])
@admin_required
def list_participants(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        return _error("Event not found", 404)

    rows = db.session.execute(
        db.select(User, Registration.registration_date)
        .join(Registration, Registration.user_id == User.id)
        .where(
            Registration.event_id == event_id,
            Registration.status == STATUS_REGISTERED,
        )
        .order_by(Registration.registration_date)
    ).all()

    return jsonify({
        "success": True,
        "participants": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "registered_at": registered_at.isoformat(),
            }
            for user, registered_at in rows
        ],
    }), 200
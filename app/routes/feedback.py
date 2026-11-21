from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.decorators import admin_required, student_required
from app.extensions import db
from app.models.event import Event
from app.models.feedback import Feedback, average_rating
from app.models.registration import STATUS_REGISTERED, Registration

feedback_bp = Blueprint("feedback", __name__)

MAX_COMMENT_LENGTH = 1000


def _error(message, status):
    return jsonify({"success": False, "message": message}), status


def _validate_feedback(data):
    """Return (rating, comments, None) if valid, or (None, None, message)."""
    if not isinstance(data, dict):
        return None, None, "Invalid request data"

    rating = data.get("rating")
    if (
        not isinstance(rating, int)
        or isinstance(rating, bool)
        or not 1 <= rating <= 5
    ):
        return None, None, "rating must be a whole number from 1 to 5"

    comments = data.get("comments")
    if comments is None:
        comments = ""
    if not isinstance(comments, str):
        return None, None, "comments must be text"

    comments = comments.strip()
    if len(comments) > MAX_COMMENT_LENGTH:
        return None, None, f"comments must be at most {MAX_COMMENT_LENGTH} characters"

    return rating, (comments or None), None


def _event_has_ended(event):
    ends_at = datetime.combine(event.event_date, event.end_time)
    return ends_at < datetime.now()


def _has_active_registration(user_id, event_id):
    registration = db.session.execute(
        db.select(Registration).filter_by(user_id=user_id, event_id=event_id)
    ).scalar_one_or_none()
    return registration is not None and registration.status == STATUS_REGISTERED


def _find_feedback(user_id, event_id):
    return db.session.execute(
        db.select(Feedback).filter_by(user_id=user_id, event_id=event_id)
    ).scalar_one_or_none()


@feedback_bp.route("/api/events/<int:event_id>/feedback", methods=["POST"])
@student_required
def submit_feedback(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        return _error("Event not found", 404)

    if not _has_active_registration(current_user.id, event_id):
        return _error("Only registered students can submit feedback", 403)

    if not _event_has_ended(event):
        return _error("Feedback is allowed only after the event has ended", 400)

    rating, comments, error = _validate_feedback(request.get_json(silent=True))
    if error:
        return _error(error, 400)

    if _find_feedback(current_user.id, event_id):
        return _error("You have already submitted feedback for this event", 409)

    feedback = Feedback(
        user_id=current_user.id,
        event_id=event_id,
        rating=rating,
        comments=comments,
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Feedback submitted",
        "feedback": feedback.to_dict(),
    }), 201


@feedback_bp.route("/api/events/<int:event_id>/feedback", methods=["PUT"])
@student_required
def edit_feedback(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        return _error("Event not found", 404)

    feedback = _find_feedback(current_user.id, event_id)
    if feedback is None:
        return _error("You have not submitted feedback for this event", 404)

    rating, comments, error = _validate_feedback(request.get_json(silent=True))
    if error:
        return _error(error, 400)

    feedback.rating = rating
    feedback.comments = comments
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Feedback updated",
        "feedback": feedback.to_dict(),
    }), 200


@feedback_bp.route("/api/events/<int:event_id>/feedback", methods=["GET"])
@admin_required
def list_feedback(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        return _error("Event not found", 404)

    entries = db.session.execute(
        db.select(Feedback)
        .where(Feedback.event_id == event_id)
        .order_by(Feedback.created_at.desc(), Feedback.id.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "feedback": [entry.to_dict() for entry in entries],
        "count": len(entries),
        "average_rating": average_rating(event_id),
    }), 200
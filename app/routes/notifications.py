from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import func


from app.decorators import admin_required, student_required
from app.extensions import db
from app.models.event import Event
from app.models.notification import Notification
from app.services.notifications import notify_registered_students

notifications_bp = Blueprint("notifications", __name__)


def _error(message, status):
    return jsonify({"success": False, "message": message}), status


def _unread_count(user_id):
    return db.session.scalar(
        db.select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )


@notifications_bp.route("/api/notifications", methods=["GET"])
@student_required
def list_notifications():
    notifications = db.session.execute(
        db.select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    ).scalars().all()

    return jsonify({
        "success": True,
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": _unread_count(current_user.id),
    }), 200


@notifications_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@student_required
def mark_as_read(notification_id):
    notification = db.session.execute(
        db.select(Notification).filter_by(
            id=notification_id, user_id=current_user.id
        )
    ).scalar_one_or_none()

    if notification is None:
        return _error("Notification not found", 404)

    notification.is_read = True
    db.session.commit()

    return jsonify({"success": True, "message": "Marked as read"}), 200


@notifications_bp.route("/api/notifications/read-all", methods=["POST"])
@student_required
def mark_all_as_read():
    db.session.execute(
        db.update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    db.session.commit()

    return jsonify({"success": True, "message": "All marked as read"}), 200


@notifications_bp.route("/api/events/<int:event_id>/announcements", methods=["POST"])
@admin_required
def publish_announcement(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        return _error("Event not found", 404)

    data = request.get_json(silent=True)
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, str) or not message.strip():
        return _error("message is required", 400)

    message = message.strip()
    if len(message) > 400:
        return _error("message must be at most 400 characters", 400)

    count = notify_registered_students(
        event, f"Announcement for {event.title}: {message}"
    )
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Announcement published",
        "notified": count,
    }), 201
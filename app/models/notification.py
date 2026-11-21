from datetime import datetime, timezone

from app.extensions import db


def _utc_now():
    return datetime.now(timezone.utc)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SET NULL: when an event is deleted, the notification stays.
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("event.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=_utc_now, nullable=False
    )
    event = db.relationship("Event", back_populates="notifications")
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }
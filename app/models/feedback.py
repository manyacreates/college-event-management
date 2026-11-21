from datetime import datetime, timezone

from sqlalchemy import func

from app.extensions import db


def _utc_now():
    return datetime.now(timezone.utc)


class Feedback(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_feedback_user_event"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating"),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.String(1000), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    event = db.relationship("Event", back_populates="feedback_entries")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "rating": self.rating,
            "comments": self.comments,
            "student_name": self.user.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def average_rating(event_id):
    """Average rating for an event, or None if nobody has given feedback."""
    value = db.session.scalar(
        db.select(func.avg(Feedback.rating)).where(Feedback.event_id == event_id)
    )
    return round(float(value), 2) if value is not None else None
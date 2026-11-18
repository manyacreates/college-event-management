from datetime import datetime, timezone

from sqlalchemy import func

from app.extensions import db

STATUS_REGISTERED = "registered"
STATUS_CANCELLED = "cancelled"


def _utc_now():
    return datetime.now(timezone.utc)


class Registration(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_registration_user_event"),
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

    registration_date = db.Column(
        db.DateTime(timezone=True), default=_utc_now, nullable=False
    )
    status = db.Column(
        db.String(20), nullable=False, default=STATUS_REGISTERED, index=True
    )

    event = db.relationship("Event", back_populates="registrations")
    user = db.relationship("User")

    def to_dict(self, include_event=False):
        data = {
            "id": self.id,
            "event_id": self.event_id,
            "status": self.status,
            "registration_date": self.registration_date.isoformat(),
        }
        if include_event:
            data["event"] = self.event.to_dict()
        return data


def count_active(event_id):
    """Number of seats taken: only 'registered' rows count."""
    return db.session.scalar(
        db.select(func.count(Registration.id)).where(
            Registration.event_id == event_id,
            Registration.status == STATUS_REGISTERED,
        )
    )
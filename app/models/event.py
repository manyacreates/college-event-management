from datetime import datetime, timezone

from app.extensions import db
from app.models.registration import count_active
CATEGORIES = [
    "Technical",
    "Cultural",
    "Sports",
    "Workshops",
    "Seminars",
    "Other",
]


def _utc_now():
    return datetime.now(timezone.utc)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)

    event_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    venue = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)

    organizer_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )
    registrations = db.relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="event",
        passive_deletes=True,
    )
    feedback_entries = db.relationship(
        "Feedback",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    def to_dict(self):
        registered_count = count_active(self.id)
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "event_date": self.event_date.isoformat(),
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
            "venue": self.venue,
            "capacity": self.capacity,
            "image_url": self.image_url,
            "organizer_id": self.organizer_id,
            "registered_count": registered_count,
            "spots_left": max(self.capacity - registered_count, 0),
        }
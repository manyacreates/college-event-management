from app.extensions import db
from app.models.notification import Notification
from app.models.registration import STATUS_REGISTERED, Registration


def notify_user(user_id, event_id, message):
    """Add a notification. The caller commits, so it joins their transaction."""
    db.session.add(
        Notification(user_id=user_id, event_id=event_id, message=message)
    )


def notify_registered_students(event, message):
    """Notify every student with an active registration for the event."""
    user_ids = db.session.execute(
        db.select(Registration.user_id).where(
            Registration.event_id == event.id,
            Registration.status == STATUS_REGISTERED,
        )
    ).scalars().all()

    for user_id in user_ids:
        notify_user(user_id, event.id, message)

    return len(user_ids)
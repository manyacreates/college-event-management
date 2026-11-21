from datetime import date, time, timedelta

from app import create_app
from app.extensions import db
from app.models.event import Event
from app.models.user import User

DEMO_EVENTS = [
    ("Annual Tech Fest", "Technical", 10, "Main Auditorium", 300),
    ("Cultural Night", "Cultural", 15, "Open Air Theatre", 500),
    ("Inter-College Cricket Cup", "Sports", 20, "College Ground", 120),
    ("Python Workshop", "Workshops", 7, "Computer Lab 3", 40),
    ("AI in Healthcare Seminar", "Seminars", 12, "Seminar Hall", 150),
    ("Photography Meetup", "Other", 25, "Library Lawn", 60),
]

app = create_app()
with app.app_context():
    admin = db.session.execute(
        db.select(User).filter_by(role="admin")
    ).scalars().first()
    if admin is None:
        raise SystemExit("Create an admin first: flask --app run create-admin")

    for title, category, days, venue, capacity in DEMO_EVENTS:
        db.session.add(Event(
            title=title,
            description="Demo event for the college event management system.",
            category=category,
            event_date=date.today() + timedelta(days=days),
            start_time=time(10, 0),
            end_time=time(16, 0),
            venue=venue,
            capacity=capacity,
            organizer_id=admin.id,
        ))
    db.session.commit()
    print("Demo events added.")
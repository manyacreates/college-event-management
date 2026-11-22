from datetime import date, datetime
from functools import wraps

from flask import Blueprint, abort, redirect, render_template
from flask_login import current_user

from app.extensions import db
from app.models.event import CATEGORIES, Event

pages_bp = Blueprint("pages", __name__)

CATEGORY_ICONS = {
    "Technical": "bi-cpu",
    "Cultural": "bi-music-note-beamed",
    "Sports": "bi-trophy",
    "Workshops": "bi-tools",
    "Seminars": "bi-mic",
    "Other": "bi-stars",
}


def page_role(role, login_url):
    """Redirect to the login page unless the user has this role."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                return redirect(login_url)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@pages_bp.app_template_filter("pretty_date")
def pretty_date(value):
    """Turn '2026-12-05' into '05 Dec 2026'."""
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")


@pages_bp.route("/")
def index():
    upcoming = db.session.execute(
        db.select(Event)
        .where(Event.event_date >= date.today())
        .order_by(Event.event_date, Event.start_time)
        .limit(6)
    ).scalars().all()

    return render_template(
        "index.html",
        events=[event.to_dict() for event in upcoming],
        categories=[(name, CATEGORY_ICONS[name]) for name in CATEGORIES],
    )


# ---------- Auth pages ----------

@pages_bp.route("/login")
def login_page():
    return render_template(
        "auth/auth.html", mode="login",
        title="Welcome back", subtitle="Log in to see your events.",
    )


@pages_bp.route("/register")
def register_page():
    return render_template(
        "auth/auth.html", mode="register",
        title="Create your account", subtitle="Join CEMS and start registering for events.",
    )


@pages_bp.route("/admin/login")
def admin_login_page():
    return render_template(
        "auth/auth.html", mode="admin",
        title="Admin login", subtitle="Organizers and administrators only.",
    )


# ---------- Public event pages ----------

@pages_bp.route("/events")
def events_page():
    return render_template("events/list.html", categories=CATEGORIES)


@pages_bp.route("/events/<int:event_id>")
def event_detail_page(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    ended = datetime.combine(event.event_date, event.end_time) < datetime.now()
    is_student = current_user.is_authenticated and current_user.role == "student"
    return render_template(
        "events/detail.html", event=event.to_dict(), ended=ended, is_student=is_student
    )


# ---------- Student pages ----------

@pages_bp.route("/dashboard")
@page_role("student", "/login")
def student_dashboard():
    return render_template("student/dashboard.html", active="dashboard")


@pages_bp.route("/notifications")
@page_role("student", "/login")
def notifications_page():
    return render_template("student/notifications.html", active="notifications")

# ---------- Admin pages ----------

@pages_bp.route("/admin/dashboard")
@page_role("admin", "/admin/login")
def admin_dashboard():
    return render_template("admin/dashboard.html", active="dashboard")


@pages_bp.route("/admin/events")
@page_role("admin", "/admin/login")
def admin_events():
    return render_template("admin/events.html", active="events", categories=CATEGORIES)


@pages_bp.route("/admin/events/<int:event_id>")
@page_role("admin", "/admin/login")
def admin_event_manage(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    return render_template("admin/manage.html", active="events", event=event.to_dict())
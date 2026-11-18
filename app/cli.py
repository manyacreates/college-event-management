import click

from app.extensions import db
from app.models.user import User


@click.command("create-admin")
@click.option("--name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True,
              confirmation_prompt=True)
def create_admin(name, email, password):
    """Create an administrator account."""
    name = name.strip()
    email = email.strip().lower()

    if not name or not email:
        raise click.ClickException("Name and email are required.")

    if len(password) < 8:
        raise click.ClickException("Password must be at least 8 characters.")

    existing = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if existing:
        raise click.ClickException("Email already registered.")

    admin = User(name=name, email=email, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    click.echo(f"Admin created: {email}")
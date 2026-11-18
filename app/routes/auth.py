from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "student")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (name, email, password, role)
    ):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    name = name.strip()
    email = email.strip().lower()
    role = role.strip().lower()

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters"
        }), 400

    if role != "student":
        return jsonify({
            "success": False,
            "message": "Only student registration is allowed"
        }), 403

    existing_user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if existing_user:
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    user = User(
        name=name,
        email=email,
        role="student"
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Registration successful"
    }), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (email, password)
    ):
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    email = email.strip().lower()

    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if user is None or not user.check_password(password):
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    login_user(user)

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": user.to_dict()
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({
        "success": True,
        "message": "Logged out"
    }), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({"success": True, "user": current_user.to_dict()}), 200
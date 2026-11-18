from functools import wraps

from flask import jsonify
from flask_login import current_user


def admin_required(view):
    """Allow only logged-in admins. Anonymous gets 401, students get 403."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401

        if current_user.role != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        return view(*args, **kwargs)

    return wrapped
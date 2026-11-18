from functools import wraps

from flask import jsonify
from flask_login import current_user


def role_required(role):
    """Allow only logged-in users with this role. Anonymous gets 401, others 403."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    "success": False,
                    "message": "Authentication required"
                }), 401

            if current_user.role != role:
                return jsonify({
                    "success": False,
                    "message": f"{role.capitalize()} access required"
                }), 403

            return view(*args, **kwargs)

        return wrapped
    return decorator


admin_required = role_required("admin")
student_required = role_required("student")
from flask import Blueprint, jsonify

from app.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/ping", methods=["GET"])
@admin_required
def ping():
    return jsonify({"success": True, "message": "pong"}), 200
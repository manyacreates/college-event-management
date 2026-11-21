from flask import Flask, jsonify

from app.cli import create_admin
from app.extensions import db, bcrypt, login_manager
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.events import events_bp
from config import DevelopmentConfig
from app.routes.registrations import registrations_bp
from app.routes.notifications import notifications_bp

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(notifications_bp)
    app.cli.add_command(create_admin)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    return app
from flask import Flask, jsonify

from app.extensions import db, bcrypt
from app.routes.auth import auth_bp


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    return app
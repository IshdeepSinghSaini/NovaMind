"""
app.py - The starting point of the NovaMind backend.

Run it from the "backend" folder:
    python app.py
Then open: http://localhost:5000/api/health
"""

from flask import Flask, jsonify

from config import Config
from database import check_connection, close_db, get_db
from extensions import jwt, limiter


def create_app(overrides=None):
    """Build and return the Flask app (called the 'app factory' pattern)."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)  # used by tests

    # ---- Connect add-ons ----
    jwt.init_app(app)
    limiter.init_app(app)
    app.teardown_appcontext(close_db)  # close the DB session after every request

    # ---- Routes ----
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        """A simple 'are you alive?' check for the server and the database."""
        db_ok, db_info = check_connection()
        return jsonify({
            "app": "NovaMind",
            "server": "running",
            "database": "connected" if db_ok else "not connected",
            "database_info": db_info,
        }), (200 if db_ok else 500)

    return app


def register_error_handlers(app):
    """Always answer with clear JSON errors (never an HTML error page or a stack trace)."""

    # ---- Login token problems -> 401 ----
    @jwt.unauthorized_loader
    def missing_token(reason):
        # Also used when the CSRF header is missing on POST/PUT/PATCH/DELETE
        return jsonify({"error": "Please log in to continue."}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Your session is not valid. Please log in again."}), 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify({"error": "Your session has expired. Please log in again."}), 401

    # ---- General errors ----
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        from services.audit_service import RATE_LIMITED, log_action
        from flask import request

        log_action(get_db(), RATE_LIMITED, details={"path": request.path, "limit": str(e.description)})
        return jsonify({"error": "Too many attempts. Please wait a minute and try again."}), 429

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Something went wrong on the server."}), 500


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)

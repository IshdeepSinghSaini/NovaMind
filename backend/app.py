"""
app.py - The starting point of the NovaMind backend.

Run it from the "backend" folder:
    python app.py
Then open: http://localhost:5000/api/health
"""

from flask import Flask, jsonify

from config import Config
from database import check_connection


def create_app():
    """Build and return the Flask app (called the 'app factory' pattern)."""
    app = Flask(__name__)
    app.config.from_object(Config)

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


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)

"""
extensions.py - Flask add-ons created once and shared by the whole app.

They are created here "empty" and connected to the app inside create_app().
This avoids circular imports (routes can import them without importing app.py).
"""

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Creates and checks login tokens (JWT)
jwt = JWTManager()

# Counts requests per IP address and blocks when the limit is reached
limiter = Limiter(key_func=get_remote_address)

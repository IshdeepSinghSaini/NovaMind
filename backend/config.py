"""
config.py - All NovaMind settings in one place.

Settings are read from the .env file (in the project root folder),
so secrets like passwords and API keys are never written inside the code.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Project root = the folder that contains "backend", "frontend", "data", ...
BASE_DIR = Path(__file__).resolve().parent.parent

# Load values from the .env file into environment variables
load_dotenv(BASE_DIR / ".env")


class Config:
    # ---- Flask ----
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

    # ---- PostgreSQL ----
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "novamind_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # URL.create() safely handles special characters (like @ or #) in the password
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

    # ---- Login (JWT stored in a secure cookie) ----
    JWT_SECRET_KEY = SECRET_KEY                   # used to sign (stamp) the login token
    JWT_TOKEN_LOCATION = ["cookies"]              # token lives in a cookie, not in JavaScript
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)  # one working day, then log in again
    JWT_COOKIE_SECURE = not DEBUG                 # HTTPS-only cookies in production
    JWT_COOKIE_SAMESITE = "Lax"                   # cookie not sent from other websites' forms
    JWT_COOKIE_CSRF_PROTECT = True                # POST/PUT/PATCH/DELETE need the CSRF header too
    JWT_SESSION_COOKIE = True                     # cookie is removed when the browser closes

    # ---- Rate limiting ----
    RATELIMIT_STORAGE_URI = "memory://"           # counters kept in memory (fine for one server)
    RATELIMIT_HEADERS_ENABLED = True              # tell the client how many tries are left
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5 per minute;20 per hour")

    # ---- Documents and chunking ----
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
    MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
    # Flask refuses any request bigger than this BEFORE reading it (+1 MB for form fields)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_BYTES + 1024 * 1024
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))        # characters per chunk
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))  # characters shared by neighbours

    # ---- Embeddings and vector store ----
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "novamind_chunks")

    # ---- Folders ----
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    VECTOR_STORE_DIR = DATA_DIR / "vector_store"
    KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
    FRONTEND_DIR = BASE_DIR / "frontend"

    # ---- AI (used from Phase 9) ----
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

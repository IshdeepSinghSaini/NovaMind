"""
config.py - All NovaMind settings in one place.

Settings are read from the .env file (in the project root folder),
so secrets like passwords and API keys are never written inside the code.
"""

import os
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

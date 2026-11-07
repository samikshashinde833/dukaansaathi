"""Vercel entrypoint. Vercel's filesystem is read-only except /tmp, so SQLite lives there (NOT permanent)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DB_PATH", "/tmp/dukaan.db")
from app.main import app  # noqa: E402

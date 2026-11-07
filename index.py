import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DB_PATH", "/tmp/dukaan.db")

from app.main import app
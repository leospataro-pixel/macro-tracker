"""Almacenamiento en ficheros JSON (compatible con un volumen persistente en Railway)."""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_DIR = Path(os.environ.get("DATA_DIR", "tracker_data"))
TZ = ZoneInfo(os.environ.get("APP_TZ", "Europe/Madrid"))

FOODS_FILE     = DATA_DIR / "foods.json"
MEALS_FILE     = DATA_DIR / "meals.json"
GOALS_FILE     = DATA_DIR / "goals.json"  # legacy (single user), migrated into users
USERS_FILE     = DATA_DIR / "users.json"
WORKOUTS_FILE  = DATA_DIR / "workouts.json"
PUSH_FILE      = DATA_DIR / "push_subscriptions.json"
SENT_FILE      = DATA_DIR / "reminders_sent.json"

_lock = threading.RLock()


def now() -> datetime:
    return datetime.now(TZ)


def today() -> str:
    return now().strftime("%Y-%m-%d")


def load(path: Path, default):
    with _lock:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return default


def save(path: Path, data):
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def load_foods() -> dict:
    return load(FOODS_FILE, {})


def load_meals() -> list:
    return load(MEALS_FILE, [])


def load_users() -> dict:
    return load(USERS_FILE, {})


def load_workouts() -> list:
    return load(WORKOUTS_FILE, [])

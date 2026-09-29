"""Notificaciones push (Web Push + VAPID) y programador de recordatorios de comidas."""

import base64
import fcntl
import json
import logging
import os
import threading
import time

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid02
from pywebpush import WebPushException, webpush

import storage
from nutrition import MEAL_EMOJI, MEAL_LABELS

log = logging.getLogger("push")

VAPID_FILE = storage.DATA_DIR / "vapid_private.pem"
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com")
# How long after the reminder time we still send it (covers restarts / sleeps)
WINDOW_MIN = 20

_vapid = None


def _get_vapid() -> Vapid02:
    global _vapid
    if _vapid is None:
        pem = os.environ.get("VAPID_PRIVATE_KEY", "").replace("\\n", "\n")
        if pem:
            _vapid = Vapid02.from_pem(pem.encode())
        elif VAPID_FILE.exists():
            _vapid = Vapid02.from_file(str(VAPID_FILE))
        else:
            storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
            _vapid = Vapid02()
            _vapid.generate_keys()
            _vapid.save_key(str(VAPID_FILE))
    return _vapid


def public_key() -> str:
    raw = _get_vapid().public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


# ── Subscriptions: {endpoint: {"user_id": ..., "subscription": {...}}} ────────

def subscribe(user_id: str, subscription: dict):
    subs = storage.load(storage.PUSH_FILE, {})
    subs[subscription["endpoint"]] = {"user_id": user_id, "subscription": subscription}
    storage.save(storage.PUSH_FILE, subs)


def unsubscribe(endpoint: str):
    subs = storage.load(storage.PUSH_FILE, {})
    if subs.pop(endpoint, None):
        storage.save(storage.PUSH_FILE, subs)


def user_has_subscription(user_id: str) -> bool:
    return any(s["user_id"] == user_id for s in storage.load(storage.PUSH_FILE, {}).values())


def send_to_user(user_id: str, title: str, body: str, url: str = "/") -> int:
    subs = storage.load(storage.PUSH_FILE, {})
    payload = json.dumps({"title": title, "body": body, "url": url})
    sent, dead = 0, []
    for endpoint, s in subs.items():
        if s["user_id"] != user_id:
            continue
        try:
            webpush(s["subscription"], payload, vapid_private_key=_get_vapid(),
                    vapid_claims={"sub": VAPID_SUBJECT}, ttl=3600, timeout=10)
            sent += 1
        except WebPushException as e:
            status = e.response.status_code if e.response is not None else None
            if status in (404, 410):
                dead.append(endpoint)
            else:
                log.warning("push failed (%s): %s", status, e)
        except Exception as e:  # network errors must not stop other reminders
            log.warning("push failed: %s", e)
    for endpoint in dead:
        unsubscribe(endpoint)
    return sent


# ── Reminder scheduler ────────────────────────────────────────────────────────

def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def check_reminders():
    now = storage.now()
    today = now.strftime("%Y-%m-%d")
    now_min = now.hour * 60 + now.minute

    sent = storage.load(storage.SENT_FILE, {})
    sent = {today: sent.get(today, [])}  # drop previous days
    meals_today = [m for m in storage.load_meals() if m["date"] == today]
    changed = False

    for uid, user in storage.load_users().items():
        for meal, hhmm in (user.get("reminders") or {}).items():
            if not hhmm:
                continue
            key = f"{uid}:{meal}"
            if key in sent[today]:
                continue
            delta = now_min - _minutes(hhmm)
            if not 0 <= delta <= WINDOW_MIN:
                continue
            sent[today].append(key)
            changed = True
            if meal == "entreno":
                send_to_user(uid, "🏋️ Hora de entrenar",
                             f"{user['name']}, toca entrenar hoy. ¡Vamos!", "/entreno")
                continue
            if any(m["user_id"] == uid and m.get("meal") == meal for m in meals_today):
                continue  # already logged
            send_to_user(uid, f"{MEAL_EMOJI.get(meal, '🍽️')} {MEAL_LABELS.get(meal, meal)}",
                         f"{user['name']}, registra tu {MEAL_LABELS.get(meal, meal).lower()} "
                         "en 10 segundos 📸", f"/registrar?comida={meal}")
    if changed:
        storage.save(storage.SENT_FILE, sent)


def _loop():
    while True:
        try:
            check_reminders()
        except Exception:  # keep the scheduler alive whatever happens
            log.exception("reminder check failed")
        time.sleep(60 - storage.now().second)


_lock_handle = None


def start_scheduler():
    """Start the reminder thread in only one process (gunicorn may fork several)."""
    global _lock_handle
    if os.environ.get("DISABLE_REMINDERS"):
        return
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _lock_handle = open(storage.DATA_DIR / ".scheduler.lock", "w")
    try:
        fcntl.flock(_lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return  # another worker owns the scheduler
    _get_vapid()
    threading.Thread(target=_loop, daemon=True, name="reminders").start()

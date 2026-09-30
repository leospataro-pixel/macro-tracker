#!/usr/bin/env python3
"""
Macro Tracker familiar – Web App (PWA)
Ejecutar: python app.py
Abrir en el móvil: http://<IP-de-tu-PC>:5000
"""

import json
import os
import uuid
from collections import Counter
from datetime import timedelta

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)

import ai
import diet
import exercises as exlib
import stretches as stlib
import push
import storage
from nutrition import (ACTIVITY, DEFAULT_REMINDERS, MACRO_KEYS, MEAL_EMOJI, MEAL_KEYS,
                       MEAL_LABELS, MEAL_TYPES, build_day_plan, calc_targets,
                       macros_for_grams, meal_for_hour, sum_macros)
from storage import load_foods, load_meals, load_users, load_workouts, save
from training import GOAL_TIPS, GOALS, LEVELS, ROUTINES_BY_ID, recommended_routines

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "calorie-tracker-key-2024")
app.permanent_session_lifetime = timedelta(days=365)
APP_PIN = os.environ.get("APP_PIN", "")

AVATARS = ["🧔", "👩", "👨", "👧", "👦", "👵", "👴", "🧑", "🦸", "🏋️"]
DEFAULT_MEALS = ["desayuno", "comida", "merienda", "cena"]
CARDIO_MET = {"Caminar": 3.5, "Correr": 9.8, "Bici": 7.0, "HIIT": 8.0,
              "Natación": 7.0, "Pádel / Fútbol": 7.0, "Otro": 5.0}

# ── Helpers ────────────────────────────────────────────────────────────────────

def new_id() -> str:
    return uuid.uuid4().hex[:8]


def bar_color(pct: int) -> str:
    if pct >= 100:
        return "danger"
    if pct >= 90:
        return "warning"
    return "success"


def to_float(value, default=None):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


app.add_template_filter(exlib.slugify, "slug")


@app.template_filter("n")
def fmt_number(value):
    """150.0 -> 150 · 12.5 -> 12.5"""
    try:
        return f"{round(float(value), 1):g}"
    except (TypeError, ValueError):
        return value if value is not None else ""


def auto_targets(user: dict) -> dict:
    """Targets from body data + goal, adjusted for health conditions."""
    base = calc_targets(user["sex"], user["age"], user["height"], user["weight"],
                        user["activity"], user["goal"])
    return {**base, **diet.adjust_targets(base, user.get("conditions", []))}


def user_prefs(user: dict) -> dict:
    return {k: user.get(k, []) for k in ("conditions", "dislike_groups", "likes", "dislikes")}


def save_user(user: dict):
    users = load_users()
    users[user["id"]] = user
    save(storage.USERS_FILE, users)


def user_meals(uid: str, date: str | None = None) -> list:
    return [m for m in load_meals()
            if m.get("user_id") == uid and (date is None or m["date"] == date)]


def by_meal(entries: list) -> dict:
    grouped = {k: [] for k in MEAL_KEYS}
    for e in entries:
        grouped.setdefault(e.get("meal", "comida"), []).append(e)
    return grouped


def add_entries(uid: str, meal: str, items: list, source: str = "manual") -> int:
    """items: dicts with food_name, grams and macros (optionally food_id)."""
    now = storage.now()
    meals = load_meals()
    for it in items:
        meals.append({
            "id": new_id(), "user_id": uid,
            "date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M"),
            "meal": meal if meal in MEAL_KEYS else meal_for_hour(now.hour),
            "food_id": it.get("food_id"), "food_name": it["food_name"],
            "grams": float(it["grams"]), "source": source,
            **{k: round(float(it.get(k) or 0), 1) for k in MACRO_KEYS},
        })
    save(storage.MEALS_FILE, meals)
    return len(items)


def macro_progress(totals: dict, targets: dict) -> list:
    rows = []
    for key, label, unit, emoji in [
        ("calories", "Calorías",      "kcal", "🔥"),
        ("protein",  "Proteínas",     "g",    "💪"),
        ("carbs",    "Carbohidratos", "g",    "🌾"),
        ("fat",      "Grasas",        "g",    "🥑"),
    ]:
        current, goal = totals[key], targets.get(key, 0)
        pct = min(int(current / goal * 100), 100) if goal > 0 else 0
        remaining = round(goal - current, 1)
        rows.append({"key": key, "label": label, "unit": unit, "emoji": emoji,
                     "current": current, "goal": goal, "pct": pct,
                     "remaining": remaining, "bar_color": bar_color(pct),
                     "over": remaining < 0})
    return rows


def frequent_foods(uid: str, meal: str, limit: int = 8) -> list:
    """Most logged foods by this user (this meal type first) with the last amount."""
    foods = load_foods()
    cutoff = (storage.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    recent = [m for m in user_meals(uid) if m["date"] >= cutoff and m.get("food_id") in foods]
    counts = Counter()
    last_grams = {}
    for m in recent:
        counts[m["food_id"]] += 3 if m.get("meal") == meal else 1
        last_grams[m["food_id"]] = m["grams"]
    return [{**foods[fid], "last_grams": last_grams[fid]}
            for fid, _ in counts.most_common(limit)]


def workouts_for(uid: str) -> list:
    return sorted((w for w in load_workouts() if w["user_id"] == uid),
                  key=lambda w: (w["date"], w.get("time", "")), reverse=True)


def next_training_day(user: dict, workouts: list):
    routine = ROUTINES_BY_ID.get(user.get("routine_id"))
    if not routine:
        return None, None
    last = next((w for w in workouts if w.get("routine_id") == routine["id"]), None)
    idx = (last["day_idx"] + 1) % len(routine["days"]) if last else 0
    return routine, idx


def day_levels(day: dict) -> dict:
    """Muscle intensity for a routine day: primary 3, secondary 1 (max across exercises)."""
    lv = {}
    for e in day["exercises"]:
        for m, v in exlib.exercise_levels(exlib.get(e["name"])).items():
            lv[m] = max(lv.get(m, 0), v)
    return lv


def weekly_counts(workouts: list, weeks: int = 8) -> list:
    """Strength + cardio sessions per ISO week (Mon-Sun), oldest first."""
    today = storage.now().date()
    monday = today - timedelta(days=today.weekday())
    out = []
    for i in range(weeks - 1, -1, -1):
        start = monday - timedelta(weeks=i)
        end = start + timedelta(days=6)
        s, e = start.isoformat(), end.isoformat()
        out.append({"label": start.strftime("%d/%m"),
                    "fuerza": sum(1 for w in workouts if s <= w["date"] <= e and w["type"] == "fuerza"),
                    "cardio": sum(1 for w in workouts if s <= w["date"] <= e and w["type"] == "cardio"),
                    "current": i == 0})
    return out


def week_workouts(workouts: list) -> int:
    since = (storage.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    return len({w["date"] for w in workouts if w["date"] >= since and w["type"] == "fuerza"})


# ── Access control: optional family PIN + active profile ──────────────────────

PUBLIC_ENDPOINTS = {"static", "service_worker", "manifest", "pin", "health"}
NO_PROFILE_ENDPOINTS = PUBLIC_ENDPOINTS | {"profiles", "choose_profile", "new_profile"}


@app.before_request
def load_profile():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return
    if APP_PIN and not session.get("pin_ok"):
        return redirect(url_for("pin", next=request.full_path))
    users = load_users()
    g.users = users
    g.user = users.get(session.get("uid"))
    if request.endpoint in NO_PROFILE_ENDPOINTS:
        return
    if not users:
        return redirect(url_for("new_profile"))
    if not g.user:
        return redirect(url_for("profiles"))


@app.context_processor
def inject_globals():
    return {"current_user": g.get("user"), "MEAL_LABELS": MEAL_LABELS, "MUSCLES": exlib.MUSCLES,
            "MEAL_EMOJI": MEAL_EMOJI, "GOALS": GOALS, "LEVELS": LEVELS}


@app.route("/pin", methods=["GET", "POST"])
def pin():
    if request.method == "POST":
        if request.form.get("pin", "") == APP_PIN:
            session.permanent = True
            session["pin_ok"] = True
            nxt = request.args.get("next", "/")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else "/")
        flash("PIN incorrecto.", "danger")
    return render_template("pin.html")


@app.route("/health")
def health():
    return "ok"


# ── PWA ────────────────────────────────────────────────────────────────────────

@app.route("/sw.js")
def service_worker():
    resp = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest",
                               mimetype="application/manifest+json")


# ── Profiles (family members) ─────────────────────────────────────────────────

def profile_from_form(form, user: dict | None = None) -> dict:
    user = dict(user or {})
    name = form.get("name", "").strip()
    if not name:
        raise ValueError("El nombre no puede estar vacío.")
    age, height, weight = (to_float(form.get(k)) for k in ("age", "height", "weight"))
    if not (age and height and weight) or not (5 <= age <= 110 and 90 <= height <= 230
                                                  and 20 <= weight <= 300):
        raise ValueError("Revisa edad, altura (cm) y peso (kg).")
    user.update({
        "name": name,
        "emoji": form.get("emoji") if form.get("emoji") in AVATARS else AVATARS[0],
        "sex": "F" if form.get("sex") == "F" else "M",
        "age": age, "height": height, "weight": weight,
        "activity": form.get("activity") if form.get("activity") in ACTIVITY else "moderate",
        "goal": form.get("goal") if form.get("goal") in GOALS else "maintain",
        "level": form.get("level") if form.get("level") in LEVELS else "beginner",
    })
    return user


@app.route("/perfiles")
def profiles():
    return render_template("profiles.html", users=list(g.users.values()))


@app.route("/perfiles/elegir/<uid>", methods=["POST"])
def choose_profile(uid):
    if uid not in g.users:
        abort(404)
    session.permanent = True
    session["uid"] = uid
    return redirect(url_for("index"))


@app.route("/perfiles/nuevo", methods=["GET", "POST"])
def new_profile():
    if request.method == "POST":
        try:
            user = profile_from_form(request.form)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("profile_form.html", user=request.form, new=True,
                                   avatars=AVATARS, activity=ACTIVITY)
        first = not g.users
        user["id"] = new_id()
        user["targets"] = auto_targets(user)
        user["auto_targets"] = True
        user["meals"] = list(DEFAULT_MEALS)
        user["reminders"] = {m: DEFAULT_REMINDERS[m] for m in DEFAULT_MEALS}
        user["routine_id"] = recommended_routines(user["goal"], user["level"])[0]["id"]
        user["weights"] = [{"date": storage.today(), "kg": user["weight"]}]
        save_user(user)
        if first:
            migrate_legacy_meals(user["id"])
        session.permanent = True
        session["uid"] = user["id"]
        flash(f"✓ Perfil de {user['name']} creado. Objetivo: "
              f"{user['targets']['calories']} kcal/día.", "success")
        return redirect(url_for("food_prefs", nuevo=1))
    return render_template("profile_form.html", user={}, new=True,
                           avatars=AVATARS, activity=ACTIVITY)


@app.route("/perfil", methods=["GET", "POST"])
def profile():
    user = g.user
    if request.method == "POST":
        try:
            updated = profile_from_form(request.form, user)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("profile"))
        if updated["weight"] != user["weight"]:
            log_weight(updated, updated["weight"])
        updated["targets"] = auto_targets(updated)
        updated["auto_targets"] = True
        save_user(updated)
        flash(f"✓ Perfil guardado. Nuevo objetivo: {updated['targets']['calories']} kcal/día.",
              "success")
        return redirect(url_for("profile"))
    weights = sorted(user.get("weights", []), key=lambda w: w["date"], reverse=True)[:10]
    return render_template("profile.html", user=user, avatars=AVATARS, activity=ACTIVITY,
                           weights=weights)


def log_weight(user: dict, kg: float):
    today = storage.today()
    weights = [w for w in user.get("weights", []) if w["date"] != today]
    weights.append({"date": today, "kg": kg})
    user["weights"] = sorted(weights, key=lambda w: w["date"])
    user["weight"] = kg


@app.route("/perfil/peso", methods=["POST"])
def add_weight():
    kg = to_float(request.form.get("kg"))
    if not kg or not 20 <= kg <= 300:
        flash("Peso no válido.", "danger")
        return redirect(request.referrer or url_for("profile"))
    user = g.user
    log_weight(user, kg)
    if user.get("auto_targets", True):
        user["targets"] = auto_targets(user)
    save_user(user)
    flash(f"✓ Peso registrado: {kg:g} kg.", "success")
    return redirect(request.referrer or url_for("profile"))


@app.route("/perfil/alimentacion", methods=["GET", "POST"])
def food_prefs():
    user = g.user
    available = {f["name"] for f in load_foods().values()}
    if request.method == "POST":
        user["conditions"] = [c for c in request.form.getlist("conditions") if c in diet.CONDITIONS]
        user["dislike_groups"] = [d for d in request.form.getlist("dislike_groups")
                                  if d in diet.DISLIKE_GROUPS]
        user["likes"], user["dislikes"] = [], []
        for name in available:
            v = request.form.get("f_" + name)
            if v == "like":
                user["likes"].append(name)
            elif v == "dislike":
                user["dislikes"].append(name)
        if user.get("auto_targets", True):
            user["targets"] = auto_targets(user)
        user.pop("plan_choices", None)
        save_user(user)
        flash("✓ Salud y preferencias guardadas. Tu plan de comidas ya las tiene en cuenta.",
              "success")
        return redirect(url_for("index") if request.args.get("nuevo") else url_for("food_prefs"))
    prefs = user_prefs(user)
    groups = {g_name: [{"name": n, "short": n.split(" (")[0],
                        "state": "like" if n in prefs["likes"] else
                                 "dislike" if n in prefs["dislikes"] else "",
                        "health": diet.health_blocked(n, prefs)} for n in names]
              for g_name, names in diet.pref_foods(available).items()}
    return render_template("food_prefs.html", user=user, conditions=diet.CONDITIONS,
                           dislike_groups=diet.DISLIKE_GROUPS, groups=groups,
                           new=bool(request.args.get("nuevo")))


@app.route("/perfiles/eliminar/<uid>", methods=["POST"])
def delete_profile(uid):
    users = load_users()
    if uid not in users:
        abort(404)
    name = users.pop(uid)["name"]
    save(storage.USERS_FILE, users)
    save(storage.MEALS_FILE, [m for m in load_meals() if m.get("user_id") != uid])
    save(storage.WORKOUTS_FILE, [w for w in load_workouts() if w["user_id"] != uid])
    if session.get("uid") == uid:
        session.pop("uid")
    flash(f"Perfil de {name} eliminado.", "info")
    return redirect(url_for("profiles"))


def migrate_legacy_meals(uid: str):
    """Meals logged before profiles existed are assigned to the first profile."""
    meals = load_meals()
    changed = False
    for m in meals:
        if not m.get("user_id"):
            m["user_id"] = uid
            m.setdefault("meal", meal_for_hour(int(m.get("time", "12:00")[:2])))
            changed = True
    if changed:
        save(storage.MEALS_FILE, meals)


@app.route("/familia")
def family():
    today = storage.today()
    meals = [m for m in load_meals() if m["date"] == today]
    all_workouts = load_workouts()
    members = []
    for u in g.users.values():
        totals = sum_macros([m for m in meals if m.get("user_id") == u["id"]])
        t = u["targets"]
        mine = [w for w in all_workouts if w["user_id"] == u["id"]]
        routine = ROUTINES_BY_ID.get(u.get("routine_id"))
        members.append({
            "user": u, "totals": totals,
            "cal_pct": min(int(totals["calories"] / t["calories"] * 100), 100) if t["calories"] else 0,
            "prot_pct": min(int(totals["protein"] / t["protein"] * 100), 100) if t["protein"] else 0,
            "logged_meals": sorted({m.get("meal") for m in meals if m.get("user_id") == u["id"]},
                                   key=lambda k: MEAL_KEYS.index(k) if k in MEAL_KEYS else 9),
            "week_workouts": week_workouts(mine),
            "week_target": routine["days_per_week"] if routine else 3,
        })
    return render_template("family.html", members=members)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    user = g.user
    today = storage.today()
    entries = user_meals(user["id"], today)
    totals = sum_macros(entries)
    grouped = by_meal(entries)
    meal_blocks = [{"key": k, "label": MEAL_LABELS[k], "emoji": MEAL_EMOJI[k],
                    "entries": grouped.get(k, []), "totals": sum_macros(grouped.get(k, []))}
                   for k in MEAL_KEYS if k in user.get("meals", DEFAULT_MEALS) or grouped.get(k)]

    workouts = workouts_for(user["id"])
    routine, day_idx = next_training_day(user, workouts)
    trained_today = any(w["date"] == today for w in workouts)
    next_levels = day_levels(routine["days"][day_idx]) if routine else {}
    return render_template(
        "index.html", next_levels=next_levels, today=today, macros=macro_progress(totals, user["targets"]),
        meal_blocks=meal_blocks, routine=routine, day_idx=day_idx,
        trained_today=trained_today, week_count=week_workouts(workouts),
        suggested_meal=meal_for_hour(storage.now().hour),
        push_enabled=push.user_has_subscription(user["id"]))


# ── Logging meals ─────────────────────────────────────────────────────────────

@app.route("/registrar", methods=["GET", "POST"])
def log_meal():
    user = g.user
    foods = load_foods()

    if request.method == "POST":
        food_id = request.form.get("food_id", "")
        meal = request.form.get("meal", "")
        grams = to_float(request.form.get("grams"), 0)
        if grams <= 0:
            flash("Introduce una cantidad válida en gramos.", "danger")
            return redirect(url_for("log_meal", comida=meal))
        if food_id not in foods:
            flash("Alimento no encontrado.", "danger")
            return redirect(url_for("log_meal", comida=meal))
        food = foods[food_id]
        macros = macros_for_grams(food, grams)
        add_entries(user["id"], meal, [{"food_id": food_id, "food_name": food["name"],
                                        "grams": grams, **macros}])
        flash(f"✓ {grams:g}g de {food['name']} → {MEAL_LABELS.get(meal, 'comida').lower()} "
              f"({macros['calories']:g} kcal · {macros['protein']:g}g prot.)", "success")
        stay = request.form.get("stay")
        if stay:
            tab = stay if stay in ("frecuentes", "buscar") else "buscar"
            return redirect(url_for("log_meal", comida=meal, tab=tab))
        return redirect(url_for("index"))

    meal = request.args.get("comida")
    if meal not in MEAL_KEYS:
        meal = meal_for_hour(storage.now().hour)
    yesterday = (storage.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    repeat_items = [m for m in user_meals(user["id"], yesterday) if m.get("meal") == meal]
    prefs = user_prefs(user)
    food_list = [{**f, "warn": diet.health_blocked(f["name"], prefs)}
                 for f in sorted(foods.values(), key=lambda f: f["name"])]
    return render_template(
        "log.html", foods=food_list,
        meal=meal, meal_types=MEAL_TYPES, frequent=frequent_foods(user["id"], meal),
        repeat_items=repeat_items, repeat_totals=sum_macros(repeat_items),
        ai_ready=ai.is_configured(), tab=request.args.get("tab", "foto"))


@app.route("/registrar/repetir", methods=["POST"])
def repeat_meal():
    meal = request.form.get("meal", "")
    yesterday = (storage.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    items = [m for m in user_meals(g.user["id"], yesterday) if m.get("meal") == meal]
    if not items:
        flash("No hay nada que repetir.", "warning")
        return redirect(url_for("log_meal", comida=meal))
    add_entries(g.user["id"], meal, items, source="repetir")
    flash(f"✓ {MEAL_LABELS[meal]} de ayer repetido ({sum_macros(items)['calories']:g} kcal).",
          "success")
    return redirect(url_for("index"))


@app.route("/foto/analizar", methods=["POST"])
def analyze_photo():
    photo = request.files.get("photo")
    description = request.form.get("description", "").strip()[:500]
    image = photo.read() if photo else None
    if not image and not description:
        return jsonify(error="Haz una foto o describe lo que has comido."), 400
    if image and len(image) > 5 * 1024 * 1024:
        return jsonify(error="La foto es demasiado grande."), 400
    media_type = photo.mimetype if photo and photo.mimetype in (
        "image/jpeg", "image/png", "image/webp", "image/gif") else "image/jpeg"
    try:
        conditions = [diet.CONDITIONS[c]["label"] for c in g.user.get("conditions", [])
                      if c in diet.CONDITIONS]
        return jsonify(ai.analyze_meal(image, media_type, description, conditions))
    except ai.AIError as e:
        return jsonify(error=str(e)), 502


@app.route("/foto/guardar", methods=["POST"])
def save_photo_meal():
    data = request.get_json(silent=True) or {}
    meal = data.get("meal", "")
    items = []
    for it in data.get("items", []):
        name = str(it.get("name", "")).strip()[:80]
        grams = to_float(it.get("grams"), 0)
        if not name or grams <= 0:
            continue
        items.append({"food_name": name, "grams": grams,
                      **{k: max(to_float(it.get(k), 0), 0) for k in MACRO_KEYS}})
    if not items:
        return jsonify(error="No hay alimentos para guardar."), 400

    # Remember new foods (per 100 g) so they appear in search and frequent lists
    foods = load_foods()
    by_name = {f["name"].lower(): f for f in foods.values()}
    for it in items:
        food = by_name.get(it["food_name"].lower())
        if not food:
            fid = new_id()
            factor = 100 / it["grams"]
            food = {"id": fid, "name": it["food_name"], "source": "ia",
                    **{k: round(it[k] * factor, 1) for k in MACRO_KEYS}}
            foods[fid] = food
            by_name[food["name"].lower()] = food
        it["food_id"] = food["id"]
    save(storage.FOODS_FILE, foods)

    add_entries(g.user["id"], meal, items, source="foto")
    total = sum_macros(items)
    flash(f"✓ {len(items)} alimentos registrados ({total['calories']:g} kcal · "
          f"{total['protein']:g}g prot.)", "success")
    return jsonify(ok=True, redirect=url_for("index"))


@app.route("/eliminar/<meal_id>", methods=["POST"])
def delete_meal(meal_id):
    meals = [m for m in load_meals()
             if not (m["id"] == meal_id and m.get("user_id") == g.user["id"])]
    save(storage.MEALS_FILE, meals)
    flash("Comida eliminada.", "info")
    return redirect(request.referrer or url_for("index"))


# ── Daily meal plan ───────────────────────────────────────────────────────────

@app.route("/plan")
def meal_plan():
    user = g.user
    today = storage.today()
    choices = plan_choices(user, request.args.get("v"))
    variant = choices["variant"]
    grouped = by_meal(user_meals(user["id"], today))
    meals = [m for m in MEAL_KEYS if m in user.get("meals", DEFAULT_MEALS) or grouped.get(m)]
    prefs = user_prefs(user)
    plan = build_day_plan(user["targets"], grouped, meals, load_foods(),
                          seed=f"{user['id']}-{today}", variant=variant,
                          prefs=prefs, overrides=choices["meals"])
    adapted = [diet.CONDITIONS[c] for c in prefs["conditions"] if c in diet.CONDITIONS]
    adapted_groups = [diet.DISLIKE_GROUPS[d] for d in prefs["dislike_groups"]
                      if d in diet.DISLIKE_GROUPS]
    return render_template("plan.html", plan=plan, variant=variant, targets=user["targets"],
                           adapted=adapted, adapted_groups=adapted_groups,
                           role_labels=diet.ROLE_LABELS)


def plan_choices(user: dict, variant_arg=None) -> dict:
    """Today's plan state: variant ('Otras opciones') and per-meal food swaps."""
    today = storage.today()
    state = user.get("plan_choices") or {}
    if state.get("date") != today:
        state = {"date": today, "variant": 0, "meals": {}}
    if variant_arg is not None:
        v = int(to_float(variant_arg, 0))
        if v != state["variant"]:
            state = {"date": today, "variant": v, "meals": {}}
            user["plan_choices"] = state
            save_user(user)
    return state


@app.route("/plan/cambiar", methods=["POST"])
def swap_plan_food():
    user = g.user
    meal, role = request.form.get("meal", ""), request.form.get("role", "")
    wanted = request.form.get("food", "")
    if meal not in MEAL_KEYS or role not in diet.ROLE_LABELS:
        abort(400)
    state = plan_choices(user)
    available = {f["name"] for f in load_foods().values()}
    cands = diet.candidates(meal, role, user_prefs(user), available)
    current = request.form.get("current", "")
    if wanted not in cands:
        # next candidate after the current one
        i = cands.index(current) if current in cands else -1
        wanted = cands[(i + 1) % len(cands)] if cands else None
    if wanted:
        state["meals"].setdefault(meal, {})[role] = wanted
        user["plan_choices"] = state
        save_user(user)
    return redirect(url_for("meal_plan") + f"#{meal}")


@app.route("/plan/registrar", methods=["POST"])
def log_plan_meal():
    meal = request.form.get("meal", "")
    try:
        items = json.loads(request.form.get("items", "[]"))
    except json.JSONDecodeError:
        items = []
    foods = load_foods()
    clean = []
    for it in items:
        food = foods.get(it.get("food_id"))
        grams = to_float(it.get("grams"), 0)
        if food and grams > 0:
            clean.append({"food_id": food["id"], "food_name": food["name"], "grams": grams,
                          **macros_for_grams(food, grams)})
    if clean:
        add_entries(g.user["id"], meal, clean, source="plan")
        flash(f"✓ {MEAL_LABELS.get(meal, 'Comida')} del plan registrado.", "success")
    return redirect(url_for("meal_plan"))


# ── Foods database ────────────────────────────────────────────────────────────

@app.route("/agregar", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre no puede estar vacío.", "danger")
            return redirect(url_for("add_food"))
        values = {k: to_float(request.form.get(k)) for k in MACRO_KEYS}
        if any(v is None for v in values.values()):
            flash("Todos los valores deben ser números.", "danger")
            return redirect(url_for("add_food"))

        foods = load_foods()
        food_id = new_id()
        foods[food_id] = {"id": food_id, "name": name, **values}
        unit_g = to_float(request.form.get("unit_g"))
        if unit_g and unit_g > 0:
            foods[food_id]["unit_g"] = unit_g
            foods[food_id]["unit_name"] = request.form.get("unit_name", "").strip() or "ud"
        save(storage.FOODS_FILE, foods)
        flash(f"✓ '{name}' añadido.", "success")
        return redirect(url_for("list_foods"))

    return render_template("add_food.html")


@app.route("/alimentos")
def list_foods():
    food_list = sorted(load_foods().values(), key=lambda f: f["name"])
    return render_template("foods.html", foods=food_list)


@app.route("/alimentos/eliminar/<food_id>", methods=["POST"])
def delete_food(food_id):
    foods = load_foods()
    food = foods.pop(food_id, None)
    if food:
        save(storage.FOODS_FILE, foods)
        flash(f"'{food['name']}' eliminado.", "info")
    return redirect(url_for("list_foods"))


@app.route("/metas", methods=["GET", "POST"])
def goals():
    user = g.user
    if request.method == "POST":
        values = {k: to_float(request.form.get(k)) for k in MACRO_KEYS}
        if any(v is None or v < 0 for v in values.values()):
            flash("Todos los valores deben ser números.", "danger")
            return redirect(url_for("goals"))
        user["targets"] = {**user["targets"], **values}
        user["auto_targets"] = False
        save_user(user)
        flash("✓ Metas guardadas.", "success")
        return redirect(url_for("goals"))

    suggested = auto_targets(user)
    return render_template("goals.html", goals=user["targets"], suggested=suggested)


@app.route("/historial")
def history():
    user = g.user
    t = user["targets"]
    days_map: dict[str, list] = {}
    for m in user_meals(user["id"]):
        days_map.setdefault(m["date"], []).append(m)

    days = []
    for d in sorted(days_map, reverse=True)[:30]:
        totals = sum_macros(days_map[d])
        pct = min(int(totals["calories"] / t["calories"] * 100), 100) if t["calories"] > 0 else 0
        days.append({"date": d, "count": len(days_map[d]), "totals": totals,
                     "cal_pct": pct, "bar_color": bar_color(pct)})
    return render_template("history.html", days=days, goals=t)


# ── Reminders & push ──────────────────────────────────────────────────────────

@app.route("/recordatorios", methods=["GET", "POST"])
def reminders():
    user = g.user
    if request.method == "POST":
        meals, rem = [], {}
        for key in MEAL_KEYS:
            if request.form.get(f"meal_{key}"):
                meals.append(key)
                hhmm = request.form.get(f"time_{key}", "")
                if request.form.get(f"remind_{key}") and len(hhmm) == 5:
                    rem[key] = hhmm
        hhmm = request.form.get("time_entreno", "")
        if request.form.get("remind_entreno") and len(hhmm) == 5:
            rem["entreno"] = hhmm
        user["meals"] = meals or list(DEFAULT_MEALS)
        user["reminders"] = rem
        save_user(user)
        flash("✓ Comidas y recordatorios guardados.", "success")
        return redirect(url_for("reminders"))
    return render_template("reminders.html", user=user, meal_types=MEAL_TYPES,
                           defaults=DEFAULT_REMINDERS)


@app.route("/push/clave")
def push_key():
    return jsonify(key=push.public_key())


@app.route("/push/suscribir", methods=["POST"])
def push_subscribe():
    sub = request.get_json(silent=True) or {}
    if not sub.get("endpoint", "").startswith("https://"):
        return jsonify(error="Suscripción no válida"), 400
    push.subscribe(g.user["id"], sub)
    return jsonify(ok=True)


@app.route("/push/baja", methods=["POST"])
def push_unsubscribe():
    push.unsubscribe((request.get_json(silent=True) or {}).get("endpoint", ""))
    return jsonify(ok=True)


@app.route("/push/probar", methods=["POST"])
def push_test():
    n = push.send_to_user(g.user["id"], "✅ Recordatorios activados",
                          "Así te avisaré para registrar tus comidas.", "/registrar")
    return jsonify(sent=n)


# ── Training ──────────────────────────────────────────────────────────────────

@app.route("/entreno")
def training():
    user = g.user
    workouts = workouts_for(user["id"])
    routine, day_idx = next_training_day(user, workouts)
    today = storage.today()
    since = (storage.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    load = exlib.muscle_load([w for w in workouts if w["date"] >= since])
    trained = sorted(((exlib.MUSCLES[m], v) for m, v in load.items() if v > 0),
                     key=lambda x: -x[1])
    return render_template(
        "training.html", routine=routine, day_idx=day_idx, workouts=workouts[:15],
        week_levels=exlib.load_levels(load), trained=trained,
        weekly=weekly_counts(workouts),
        next_levels=day_levels(routine["days"][day_idx]) if routine else {},
        week_count=week_workouts(workouts), trained_today=any(w["date"] == today for w in workouts),
        cardio_types=list(CARDIO_MET))


@app.route("/entreno/rutinas")
def routines():
    user = g.user
    return render_template("routines.html",
                           routines=recommended_routines(user["goal"], user.get("level")),
                           tips=GOAL_TIPS.get(user["goal"], []))


@app.route("/entreno/rutinas/<rid>", methods=["POST"])
def choose_routine(rid):
    if rid not in ROUTINES_BY_ID:
        abort(404)
    g.user["routine_id"] = rid
    save_user(g.user)
    flash(f"✓ Rutina activa: {ROUTINES_BY_ID[rid]['name']}.", "success")
    return redirect(url_for("training"))


def last_sets_by_exercise(workouts: list) -> dict:
    last = {}
    for w in workouts:  # newest first
        for e in w.get("exercises", []):
            if e["name"] not in last and e["sets"]:
                last[e["name"]] = e["sets"]
    return last


@app.route("/entreno/sesion/<int:day_idx>", methods=["GET", "POST"])
def workout_session(day_idx):
    user = g.user
    routine = ROUTINES_BY_ID.get(user.get("routine_id"))
    if not routine or not 0 <= day_idx < len(routine["days"]):
        return redirect(url_for("routines"))
    day = routine["days"][day_idx]

    if request.method == "POST":
        exercises = []
        for i, e in enumerate(day["exercises"]):
            sets = []
            for j in range(e["sets"] + 1):  # +1 optional extra set
                kg = to_float(request.form.get(f"e{i}_s{j}_kg"))
                reps = to_float(request.form.get(f"e{i}_s{j}_reps"))
                if reps:
                    sets.append({"kg": kg or 0, "reps": reps})
            if sets:
                exercises.append({"name": e["name"], "sets": sets})
        if not exercises:
            flash("Apunta al menos una serie (repeticiones).", "warning")
            return redirect(url_for("workout_session", day_idx=day_idx))
        now = storage.now()
        workouts = load_workouts()
        workouts.append({
            "id": new_id(), "user_id": user["id"], "type": "fuerza",
            "date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M"),
            "routine_id": routine["id"], "day_idx": day_idx, "day_name": day["name"],
            "minutes": to_float(request.form.get("minutes"), 0),
            "notes": request.form.get("notes", "").strip()[:300],
            "exercises": exercises,
            "volume": round(sum(s["kg"] * s["reps"] for e in exercises for s in e["sets"])),
        })
        save(storage.WORKOUTS_FILE, workouts)
        flash(f"💪 ¡{day['name']} completado! {len(exercises)} ejercicios. "
              "Ahora 5 minutos de estiramientos 🧘", "success")
        return redirect(url_for("training"))

    infos = [exlib.get(e["name"]) for e in day["exercises"]]
    return render_template("workout.html", routine=routine, day=day, day_idx=day_idx,
                           infos=infos, levels=[exlib.exercise_levels(i) for i in infos],
                           day_levels=day_levels(day),
                           last=last_sets_by_exercise(workouts_for(user["id"])))


@app.route("/estiramientos")
def stretching():
    routines = [{**r, "minutes": stlib.routine_minutes(r),
                 "stretches": [stlib.BY_SLUG[s] for s in r["items"]]} for r in stlib.ROUTINES]
    items = [{**s, "photo": exlib.image_for(s["slug"]),
              "levels": exlib.exercise_levels(s)} for s in stlib.STRETCHES]
    return render_template("stretching.html", routines=routines, items=items)


@app.route("/estiramientos/<rid>")
def stretch_session(rid):
    routine = stlib.ROUTINES_BY_ID.get(rid)
    if not routine:
        abort(404)
    steps = [{**s, "photo": exlib.image_for(s["slug"]), "levels": exlib.exercise_levels(s)}
             for s in stlib.routine_steps(routine)]
    return render_template("stretch_session.html", routine=routine, steps=steps)


@app.route("/entreno/ejercicios")
def exercise_library():
    group = request.args.get("grupo", "")
    muscles = exlib.MUSCLE_GROUPS.get(group)
    items = []
    for name in sorted(exlib.EXERCISES):
        info = exlib.get(name)
        if muscles and not set(info["primary"]) & set(muscles):
            continue
        items.append({**info, "levels": exlib.exercise_levels(info)})
    return render_template("exercises.html", items=items, groups=list(exlib.MUSCLE_GROUPS),
                           group=group)


@app.route("/entreno/ejercicio/<slug>")
def exercise_detail(slug):
    name = exlib.BY_SLUG.get(slug)
    if not name:
        abort(404)
    info = exlib.get(name)
    history = []
    for w in workouts_for(g.user["id"]):
        for e in w.get("exercises", []):
            if e["name"] == name:
                best = max(e["sets"], key=lambda s: (s["kg"], s["reps"]))
                history.append({"date": w["date"], "sets": e["sets"], "best": best})
    return render_template("exercise.html", info=info, levels=exlib.exercise_levels(info),
                           history=history[:10])


@app.route("/entreno/cardio", methods=["POST"])
def log_cardio():
    kind = request.form.get("kind", "Otro")
    minutes = to_float(request.form.get("minutes"), 0)
    if minutes <= 0 or kind not in CARDIO_MET:
        flash("Indica actividad y minutos.", "danger")
        return redirect(url_for("training"))
    kcal = round(CARDIO_MET[kind] * g.user["weight"] * minutes / 60)
    now = storage.now()
    workouts = load_workouts()
    workouts.append({"id": new_id(), "user_id": g.user["id"], "type": "cardio",
                     "date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M"),
                     "day_name": kind, "minutes": minutes, "kcal": kcal, "exercises": []})
    save(storage.WORKOUTS_FILE, workouts)
    flash(f"✓ {kind} {minutes:g} min (~{kcal} kcal).", "success")
    return redirect(url_for("training"))


@app.route("/entreno/eliminar/<wid>", methods=["POST"])
def delete_workout(wid):
    save(storage.WORKOUTS_FILE, [w for w in load_workouts()
                                 if not (w["id"] == wid and w["user_id"] == g.user["id"])])
    flash("Entreno eliminado.", "info")
    return redirect(url_for("training"))


# ── Seed ───────────────────────────────────────────────────────────────────────

# name, kcal, protein, carbs, fat (per 100 g), optional (unit grams, unit name)
STARTER_FOODS = [
    ("Pechuga de pollo (cocida)",   165, 31,   0,    3.6),
    ("Arroz blanco (cocido)",       130, 2.7,  28,   0.3),
    ("Huevo entero",                155, 13,   1.1,  11,   60,  "huevo"),
    ("Avena (cruda)",               389, 17,   66,   7),
    ("Plátano",                      89, 1.1,  23,   0.3,  120, "plátano"),
    ("Manzana",                      52, 0.3,  14,   0.2,  180, "manzana"),
    ("Leche entera",                 61, 3.2,  4.8,  3.3,  250, "vaso"),
    ("Yogur natural",                59, 3.5,  3.6,  3.3,  125, "yogur"),
    ("Pan integral",                247, 13,   41,   4.2,  30,  "rebanada"),
    ("Atún en agua (escurrido)",    116, 26,   0,    1.0,  56,  "lata"),
    ("Salmón (crudo)",              208, 20,   0,    13),
    ("Brócoli (cocido)",             35, 2.4,  7.2,  0.4),
    ("Espinacas (crudas)",           23, 2.9,  3.6,  0.4),
    ("Almendras",                   579, 21,   22,   50),
    ("Aceite de oliva",             884, 0,    0,    100,  10,  "cucharada"),
    ("Patata (hervida)",             86, 1.9,  20,   0.1),
    ("Pasta (cocida)",              131, 5.0,  25,   1.1),
    ("Queso fresco 0%",              60, 12,   3.5,  0),
    ("Proteína en polvo (whey)",    400, 80,   8,    5,    30,  "cacito"),
    ("Ternera (carne magra)",       215, 26,   0,    12),
    ("Lentejas (cocidas)",          116, 9.0,  20,   0.4),
    ("Aguacate",                    160, 2.0,  9.0,  15),
    ("Naranja",                      47, 0.9,  12,   0.1,  150, "naranja"),
    ("Nueces",                      654, 15,   14,   65),
    ("Tomate",                       18, 0.9,  3.9,  0.2),
    ("Pechuga de pavo (fiambre)",   105, 21,   1.5,  1.5),
    ("Claras de huevo",              52, 11,   0.7,  0.2,  33,  "clara"),
    ("Queso fresco batido 0%",       46, 8.0,  3.5,  0.2),
    ("Tortitas de arroz",           387, 8.0,  81,   3.0,  8,   "tortita"),
    ("Merluza (cocida)",             90, 18,   0,    1.5),
    ("Garbanzos (cocidos)",         164, 8.9,  27,   2.6),
    ("Quinoa (cocida)",             120, 4.4,  21,   1.9),
    ("Boniato (asado)",              90, 2.0,  21,   0.2),
    ("Jamón serrano",               241, 31,   0,    13),
    ("Crema de cacahuete",          588, 25,   20,   50,   15,  "cucharada"),
    ("Ensalada mixta",               20, 1.0,  3.5,  0.2),
    ("Frutos rojos",                 50, 0.8,  12,   0.3),
    ("Tortilla de trigo (wrap)",    300, 8.0,  50,   7.0,  60,  "wrap"),
    ("Kiwi",                         61, 1.1,  15,   0.5,  75,  "kiwi"),
    ("Arroz integral (cocido)",     123, 2.7,  26,   1.0),
    ("Lomo de cerdo",               160, 28,   0,    5.0),
    ("Hummus",                      177, 7.9,  14,   9.6),
]


def seed_foods():
    """Adds any missing starter food (by name) and fills in unit sizes."""
    foods = load_foods()
    by_name = {f["name"]: f for f in foods.values()}
    added = 0
    for name, cal, prot, carbs, fat, *unit in STARTER_FOODS + diet.EXTRA_FOODS:
        food = by_name.get(name)
        if not food:
            fid = new_id()
            food = foods[fid] = {"id": fid, "name": name, "calories": cal,
                                 "protein": prot, "carbs": carbs, "fat": fat}
            added += 1
        if unit and "unit_g" not in food:
            food["unit_g"], food["unit_name"] = unit
    save(storage.FOODS_FILE, foods)
    if added:
        print(f"✓ Base de datos: {added} alimentos añadidos.")


# Runs at import time so gunicorn workers also get seeded data
storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
seed_foods()
push.start_scheduler()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

#!/usr/bin/env python3
"""
Calorie Tracker – Web App
Ejecutar: python calorie_web.py
Abrir en el móvil: http://<IP-de-tu-PC>:5000
"""

import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "calorie-tracker-key-2024")

# DATA_DIR can be overridden via env var (e.g. a persistent volume on Railway)
DATA_DIR = Path(os.environ.get("DATA_DIR", "tracker_data"))
FOODS_FILE = DATA_DIR / "foods.json"
MEALS_FILE = DATA_DIR / "meals.json"
GOALS_FILE = DATA_DIR / "goals.json"

# ── Storage ────────────────────────────────────────────────────────────────────

def _load(path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _save(path, data):
    DATA_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_foods() -> dict:
    return _load(FOODS_FILE, {})

def load_meals() -> list:
    return _load(MEALS_FILE, [])

def load_goals() -> dict:
    return _load(GOALS_FILE, {"calories": 2000, "protein": 150, "carbs": 200, "fat": 65})

# ── Calculations ───────────────────────────────────────────────────────────────

def macros_for_grams(food: dict, grams: float) -> dict:
    f = grams / 100
    return {
        "calories": round(food["calories"] * f, 1),
        "protein":  round(food["protein"]  * f, 1),
        "carbs":    round(food["carbs"]    * f, 1),
        "fat":      round(food["fat"]      * f, 1),
    }


def sum_macros(entries: list) -> dict:
    total = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for e in entries:
        for k in total:
            total[k] += e.get(k, 0)
    return {k: round(v, 1) for k, v in total.items()}


def bar_color(pct: int) -> str:
    if pct >= 100:
        return "danger"
    if pct >= 90:
        return "warning"
    return "success"

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    today = date.today().strftime("%Y-%m-%d")
    meals_today = [m for m in load_meals() if m["date"] == today]
    goals = load_goals()
    totals = sum_macros(meals_today)

    macros = []
    for key, label, unit, emoji in [
        ("calories", "Calorías",      "kcal", "🔥"),
        ("protein",  "Proteínas",     "g",    "💪"),
        ("carbs",    "Carbohidratos", "g",    "🌾"),
        ("fat",      "Grasas",        "g",    "🥑"),
    ]:
        current = totals[key]
        goal = goals[key]
        pct = min(int(current / goal * 100), 100) if goal > 0 else 0
        remaining = round(goal - current, 1)
        macros.append({
            "key": key, "label": label, "unit": unit, "emoji": emoji,
            "current": current, "goal": goal, "pct": pct,
            "remaining": remaining, "bar_color": bar_color(pct),
            "over": remaining < 0,
        })

    return render_template("index.html", today=today, meals=meals_today, macros=macros)


@app.route("/registrar", methods=["GET", "POST"])
def log_meal():
    foods = load_foods()
    food_list = sorted(foods.values(), key=lambda f: f["name"])

    if request.method == "POST":
        food_id = request.form.get("food_id", "")
        try:
            grams = float(request.form.get("grams", 0))
            if grams <= 0:
                raise ValueError
        except ValueError:
            flash("Introduce una cantidad válida en gramos.", "danger")
            return redirect(url_for("log_meal"))

        if food_id not in foods:
            flash("Alimento no encontrado.", "danger")
            return redirect(url_for("log_meal"))

        food = foods[food_id]
        macros = macros_for_grams(food, grams)
        now = datetime.now()
        entry = {
            "id":        str(uuid.uuid4())[:8],
            "date":      now.strftime("%Y-%m-%d"),
            "time":      now.strftime("%H:%M"),
            "food_id":   food_id,
            "food_name": food["name"],
            "grams":     grams,
            **macros,
        }
        meals = load_meals()
        meals.append(entry)
        _save(MEALS_FILE, meals)

        flash(
            f"✓ {grams:g}g de {food['name']} registrados "
            f"({macros['calories']} kcal · {macros['protein']}g prot.)",
            "success",
        )
        return redirect(url_for("index"))

    return render_template("log.html", foods=food_list)


@app.route("/agregar", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre no puede estar vacío.", "danger")
            return redirect(url_for("add_food"))
        try:
            calories = float(request.form["calories"])
            protein  = float(request.form["protein"])
            carbs    = float(request.form["carbs"])
            fat      = float(request.form["fat"])
        except (ValueError, KeyError):
            flash("Todos los valores deben ser números.", "danger")
            return redirect(url_for("add_food"))

        foods = load_foods()
        food_id = str(uuid.uuid4())[:8]
        foods[food_id] = {
            "id": food_id, "name": name,
            "calories": calories, "protein": protein,
            "carbs": carbs, "fat": fat,
        }
        _save(FOODS_FILE, foods)
        flash(f"✓ '{name}' añadido.", "success")
        return redirect(url_for("list_foods"))

    return render_template("add_food.html")


@app.route("/alimentos")
def list_foods():
    food_list = sorted(load_foods().values(), key=lambda f: f["name"])
    return render_template("foods.html", foods=food_list)


@app.route("/metas", methods=["GET", "POST"])
def goals():
    current = load_goals()
    if request.method == "POST":
        try:
            new = {
                "calories": float(request.form["calories"]),
                "protein":  float(request.form["protein"]),
                "carbs":    float(request.form["carbs"]),
                "fat":      float(request.form["fat"]),
            }
        except (ValueError, KeyError):
            flash("Todos los valores deben ser números.", "danger")
            return redirect(url_for("goals"))
        _save(GOALS_FILE, new)
        flash("✓ Metas guardadas.", "success")
        return redirect(url_for("goals"))

    return render_template("goals.html", goals=current)


@app.route("/historial")
def history():
    all_meals = load_meals()
    g = load_goals()

    by_date: dict[str, list] = {}
    for m in all_meals:
        by_date.setdefault(m["date"], []).append(m)

    days = []
    for d in sorted(by_date.keys(), reverse=True)[:30]:
        t = sum_macros(by_date[d])
        pct = min(int(t["calories"] / g["calories"] * 100), 100) if g["calories"] > 0 else 0
        days.append({
            "date": d,
            "count": len(by_date[d]),
            "totals": t,
            "cal_pct": pct,
            "bar_color": bar_color(pct),
        })

    return render_template("history.html", days=days, goals=g)


@app.route("/eliminar/<meal_id>", methods=["POST"])
def delete_meal(meal_id):
    meals = [m for m in load_meals() if m["id"] != meal_id]
    _save(MEALS_FILE, meals)
    flash("Comida eliminada.", "info")
    return redirect(url_for("index"))


# ── Seed ───────────────────────────────────────────────────────────────────────

STARTER_FOODS = [
    ("Pechuga de pollo (cocida)",   165, 31,   0,    3.6),
    ("Arroz blanco (cocido)",       130, 2.7,  28,   0.3),
    ("Huevo entero",                155, 13,   1.1,  11),
    ("Avena (cruda)",               389, 17,   66,   7),
    ("Plátano",                      89, 1.1,  23,   0.3),
    ("Manzana",                      52, 0.3,  14,   0.2),
    ("Leche entera",                 61, 3.2,  4.8,  3.3),
    ("Yogur natural",                59, 3.5,  3.6,  3.3),
    ("Pan integral",                247, 13,   41,   4.2),
    ("Atún en agua (escurrido)",    116, 26,   0,    1.0),
    ("Salmón (crudo)",              208, 20,   0,    13),
    ("Brócoli (cocido)",             35, 2.4,  7.2,  0.4),
    ("Espinacas (crudas)",           23, 2.9,  3.6,  0.4),
    ("Almendras",                   579, 21,   22,   50),
    ("Aceite de oliva",             884, 0,    0,    100),
    ("Patata (hervida)",             86, 1.9,  20,   0.1),
    ("Pasta (cocida)",              131, 5.0,  25,   1.1),
    ("Queso fresco 0%",              60, 12,   3.5,  0),
    ("Proteína en polvo (whey)",    400, 80,   8,    5),
    ("Ternera (carne magra)",       215, 26,   0,    12),
    ("Lentejas (cocidas)",          116, 9.0,  20,   0.4),
    ("Aguacate",                    160, 2.0,  9.0,  15),
    ("Naranja",                      47, 0.9,  12,   0.1),
    ("Nueces",                      654, 15,   14,   65),
    ("Tomate",                       18, 0.9,  3.9,  0.2),
]


def seed_foods():
    foods = load_foods()
    if foods:
        return
    for name, cal, prot, carbs, fat in STARTER_FOODS:
        fid = str(uuid.uuid4())[:8]
        foods[fid] = {"id": fid, "name": name,
                      "calories": cal, "protein": prot,
                      "carbs": carbs, "fat": fat}
    _save(FOODS_FILE, foods)
    print(f"✓ Base de datos inicializada con {len(STARTER_FOODS)} alimentos.")


# Runs at import time so gunicorn workers also get seeded data
DATA_DIR.mkdir(exist_ok=True)
seed_foods()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

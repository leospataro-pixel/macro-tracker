"""Cálculo de objetivos de macros y generador del plan de comidas diario."""

import hashlib

import diet

MEAL_TYPES = [
    # key,        label,          emoji, share of daily macros, default reminder
    ("desayuno", "Desayuno",      "🍳", 0.25, "08:30"),
    ("almuerzo", "Media mañana",  "🍎", 0.10, "11:30"),
    ("comida",   "Comida",        "🍽️", 0.30, "14:00"),
    ("merienda", "Merienda",      "🥪", 0.10, "17:30"),
    ("cena",     "Cena",          "🌙", 0.25, "21:00"),
]
MEAL_KEYS = [m[0] for m in MEAL_TYPES]
MEAL_LABELS = {m[0]: m[1] for m in MEAL_TYPES}
MEAL_EMOJI = {m[0]: m[2] for m in MEAL_TYPES}
MEAL_SHARE = {m[0]: m[3] for m in MEAL_TYPES}
DEFAULT_REMINDERS = {m[0]: m[4] for m in MEAL_TYPES}

ACTIVITY = {
    "sedentary": ("Sedentario (oficina, poco movimiento)", 1.2),
    "light":     ("Ligero (1-2 entrenos/semana)",          1.375),
    "moderate":  ("Moderado (3-4 entrenos/semana)",        1.55),
    "active":    ("Activo (5-6 entrenos o trabajo físico)", 1.725),
    "very":      ("Muy activo (doble sesión / trabajo duro)", 1.9),
}

GOAL_FACTOR = {"lose": 0.80, "maintain": 1.00, "recomp": 1.00, "gain": 1.10}
PROTEIN_PER_KG = {"lose": 2.2, "maintain": 1.8, "recomp": 2.0, "gain": 1.9}

MACRO_KEYS = ("calories", "protein", "carbs", "fat")


def meal_for_hour(hour: int) -> str:
    """Tipo de comida más probable según la hora (para preseleccionar)."""
    if hour < 11:
        return "desayuno"
    if hour < 13:
        return "almuerzo"
    if hour < 17:
        return "comida"
    if hour < 20:
        return "merienda"
    return "cena"


def calc_targets(sex: str, age: float, height: float, weight: float,
                 activity: str, goal: str) -> dict:
    """Mifflin-St Jeor × actividad × objetivo; proteína por kg, 27% grasa, resto carbs."""
    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if sex == "M" else -161)
    tdee = bmr * ACTIVITY.get(activity, ACTIVITY["moderate"])[1]
    kcal = round(tdee * GOAL_FACTOR.get(goal, 1.0) / 10) * 10
    protein = round(weight * PROTEIN_PER_KG.get(goal, 1.8))
    fat = round(max(kcal * 0.27 / 9, weight * 0.7))
    carbs = max(round((kcal - protein * 4 - fat * 9) / 4), 0)
    return {"calories": kcal, "protein": protein, "carbs": carbs, "fat": fat,
            "bmr": round(bmr), "tdee": round(tdee)}


# ── Meal plan ─────────────────────────────────────────────────────────────────
# Each meal = one food per role (protein / carbs / fat, plus fixed fruit or veg)
# picked from diet.POOLS according to the person's health conditions and likes.
# Grams are solved so the meal hits its share of the remaining macros.

MAX_GRAMS = {"Aceite de oliva": 30, "Crema de cacahuete": 40, "Almendras": 40,
             "Nueces": 40, "Proteína en polvo (whey)": 60, "Proteína vegetal en polvo": 60,
             "Huevo entero": 180, "Aguacate": 120, "Pan integral": 150, "Pan sin gluten": 150,
             "Tortitas de arroz": 60, "Avena (cruda)": 120, "Avena sin gluten (cruda)": 120,
             "Yogur de soja natural": 250, "Yogur natural": 250, "Queso fresco batido 0%": 350,
             "Edamame": 200, "Huevo entero": 180}
SOLVED = ("protein", "carbs", "fat")


def macros_for_grams(food: dict, grams: float) -> dict:
    f = grams / 100
    return {k: round(food[k] * f, 1) for k in MACRO_KEYS}


def sum_macros(entries: list) -> dict:
    total = dict.fromkeys(MACRO_KEYS, 0.0)
    for e in entries:
        for k in total:
            total[k] += e.get(k, 0) or 0
    return {k: round(v, 1) for k, v in total.items()}


def short_name(name: str) -> str:
    return name.split(" (")[0]


def choose_foods(meal: str, prefs: dict, available: set, seed: str, variant: int,
                 overrides: dict, used: set) -> tuple[dict, dict]:
    """One food per role. Returns (picks, alternatives)."""
    h = int(hashlib.md5(f"{seed}-{meal}".encode()).hexdigest(), 16)
    likes = set(prefs.get("likes", []))
    picks, alts = {}, {}
    for role in diet.POOLS[diet.MEAL_POOL[meal]]:
        cands = diet.candidates(meal, role, prefs, available)
        if not cands:
            continue
        choice = overrides.get(role)
        if choice not in cands:
            liked = [c for c in cands if c in likes]
            base = liked or cands
            k = (h + variant + len(role)) % len(base)
            rotated = base[k:] + base[:k]
            fresh = [c for c in rotated if c not in used] or rotated
            choice = fresh[0]
        picks[role] = choice
        alts[role] = [c for c in cands if c != choice]
    return picks, alts


def solve_meal(picks: dict, target: dict, foods_by_name: dict) -> list:
    """Grams for protein/carbs/fat foods so the meal hits the target macros."""
    fixed = [(role, foods_by_name[n], diet.FIXED_GRAMS[role])
             for role, n in picks.items() if role in diet.FIXED_GRAMS]
    slots = [(role, foods_by_name[picks[role]]) for role in SOLVED if role in picks]

    base = sum_macros([macros_for_grams(f, g) for _, f, g in fixed])
    grams = [0.0] * len(slots)
    for _ in range(25):  # Gauss-Seidel: each food covers "its" macro
        for i, (macro, food) in enumerate(slots):
            other = base[macro] + sum(
                slots[j][1][macro] * grams[j] / 100 for j in range(len(slots)) if j != i)
            per_g = food[macro] / 100
            g = (target[macro] - other) / per_g if per_g > 0 else 0
            grams[i] = min(max(g, 0), MAX_GRAMS.get(food["name"], 400))

    items = [(role, f, g) for role, f, g in fixed]
    items += [(slots[i][0], slots[i][1], grams[i]) for i in range(len(slots))]
    out = []
    for role, food, g in items:
        g = round(g / 5) * 5
        if g < 5:
            continue
        entry = {"role": role, "food_id": food["id"], "food_name": food["name"], "grams": g,
                 **macros_for_grams(food, g)}
        if food.get("unit_g"):
            entry["units"] = round(g / food["unit_g"], 1)
            entry["unit_name"] = food.get("unit_name", "ud")
        out.append(entry)
    order = ["protein", "carbs", "veg", "fruit", "fat"]
    return sorted(out, key=lambda e: order.index(e["role"]))


def meal_name(picks: dict) -> str:
    parts = [short_name(picks[r]) for r in ("protein", "carbs") if r in picks]
    extra = [short_name(picks[r]).lower() for r in ("veg", "fruit") if r in picks]
    name = " con ".join([parts[0], parts[1].lower()]) if len(parts) == 2 else "".join(parts)
    return name + (" y " + extra[0] if extra else "")


def build_day_plan(targets: dict, consumed_by_meal: dict, meals: list, foods: dict,
                   seed: str, variant: int = 0, prefs: dict | None = None,
                   overrides: dict | None = None) -> dict:
    """Plan for the meals not logged yet today, sized to the remaining macros."""
    prefs = prefs or {}
    overrides = overrides or {}
    foods_by_name = {f["name"]: f for f in foods.values()}
    available = set(foods_by_name)
    eaten = sum_macros([m for items in consumed_by_meal.values() for m in items])
    remaining = {k: max(targets[k] - eaten[k], 0) for k in MACRO_KEYS}

    pending = [m for m in meals if not consumed_by_meal.get(m)]
    share_total = sum(MEAL_SHARE[m] for m in pending) or 1

    plan, used = [], set()
    for m in meals:
        if consumed_by_meal.get(m):
            plan.append({"meal": m, "done": True, "entries": consumed_by_meal[m],
                         "totals": sum_macros(consumed_by_meal[m])})
            continue
        share = MEAL_SHARE[m] / share_total
        target = {k: remaining[k] * share for k in MACRO_KEYS}
        picks, alts = choose_foods(m, prefs, available, seed, variant,
                                   overrides.get(m, {}), used)
        if "protein" not in picks or "carbs" not in picks:
            continue
        used.add(picks["protein"])
        entries = solve_meal(picks, target, foods_by_name)
        plan.append({"meal": m, "done": False, "name": meal_name(picks), "entries": entries,
                     "alternatives": alts, "target": {k: round(v) for k, v in target.items()},
                     "totals": sum_macros(entries)})
    return {"meals": plan, "remaining": {k: round(v) for k, v in remaining.items()},
            "eaten": eaten}

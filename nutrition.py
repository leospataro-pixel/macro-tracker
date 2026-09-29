"""Cálculo de objetivos de macros y generador del plan de comidas diario."""

import hashlib

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
# Each option: protein source, carb source, fat source (optional) whose grams
# are solved to hit the target, plus fixed items (veg/fruit) with set grams.

PLAN_TEMPLATES = {
    "desayuno": [
        {"name": "Porridge proteico", "p": "Proteína en polvo (whey)", "c": "Avena (cruda)",
         "f": "Crema de cacahuete", "fixed": [("Plátano", 120)]},
        {"name": "Tostadas con pavo y aguacate", "p": "Pechuga de pavo (fiambre)",
         "c": "Pan integral", "f": "Aguacate", "fixed": [("Tomate", 60)]},
        {"name": "Tortilla con tostada y naranja", "p": "Claras de huevo", "c": "Pan integral",
         "f": "Huevo entero", "fixed": [("Naranja", 150)]},
        {"name": "Queso batido con avena y frutos rojos", "p": "Queso fresco batido 0%",
         "c": "Avena (cruda)", "f": "Nueces", "fixed": [("Frutos rojos", 100)]},
    ],
    "almuerzo": [
        {"name": "Queso batido con plátano y almendras", "p": "Queso fresco batido 0%",
         "c": "Plátano", "f": "Almendras", "fixed": []},
        {"name": "Tortitas de arroz con pavo", "p": "Pechuga de pavo (fiambre)",
         "c": "Tortitas de arroz", "f": None, "fixed": []},
        {"name": "Batido de proteína con manzana", "p": "Proteína en polvo (whey)",
         "c": "Manzana", "f": "Nueces", "fixed": []},
        {"name": "Bocadillo de jamón", "p": "Jamón serrano", "c": "Pan integral",
         "f": None, "fixed": [("Tomate", 40)]},
    ],
    "comida": [
        {"name": "Pollo con arroz y brócoli", "p": "Pechuga de pollo (cocida)",
         "c": "Arroz blanco (cocido)", "f": "Aceite de oliva", "fixed": [("Brócoli (cocido)", 150)]},
        {"name": "Lentejas con ternera", "p": "Ternera (carne magra)", "c": "Lentejas (cocidas)",
         "f": "Aceite de oliva", "fixed": [("Tomate", 80)]},
        {"name": "Salmón con patata y ensalada", "p": "Salmón (crudo)", "c": "Patata (hervida)",
         "f": "Aceite de oliva", "fixed": [("Ensalada mixta", 150)]},
        {"name": "Pasta con atún y tomate", "p": "Atún en agua (escurrido)", "c": "Pasta (cocida)",
         "f": "Aceite de oliva", "fixed": [("Tomate", 100)]},
        {"name": "Garbanzos con pollo y espinacas", "p": "Pechuga de pollo (cocida)",
         "c": "Garbanzos (cocidos)", "f": "Aceite de oliva", "fixed": [("Espinacas (crudas)", 80)]},
    ],
    "merienda": [
        {"name": "Yogur con fruta y nueces", "p": "Queso fresco batido 0%", "c": "Manzana",
         "f": "Nueces", "fixed": []},
        {"name": "Tostada con pavo", "p": "Pechuga de pavo (fiambre)", "c": "Pan integral",
         "f": "Aceite de oliva", "fixed": []},
        {"name": "Batido de proteína con plátano", "p": "Proteína en polvo (whey)",
         "c": "Plátano", "f": "Crema de cacahuete", "fixed": []},
        {"name": "Tortitas con crema de cacahuete", "p": "Queso fresco batido 0%",
         "c": "Tortitas de arroz", "f": "Crema de cacahuete", "fixed": []},
    ],
    "cena": [
        {"name": "Merluza con boniato y ensalada", "p": "Merluza (cocida)", "c": "Boniato (asado)",
         "f": "Aceite de oliva", "fixed": [("Ensalada mixta", 150)]},
        {"name": "Tortilla de espinacas con pan", "p": "Claras de huevo", "c": "Pan integral",
         "f": "Huevo entero", "fixed": [("Espinacas (crudas)", 100)]},
        {"name": "Wrap de pollo y aguacate", "p": "Pechuga de pollo (cocida)",
         "c": "Tortilla de trigo (wrap)", "f": "Aguacate", "fixed": [("Ensalada mixta", 80)]},
        {"name": "Salmón con quinoa y brócoli", "p": "Salmón (crudo)", "c": "Quinoa (cocida)",
         "f": None, "fixed": [("Brócoli (cocido)", 150)]},
    ],
}

MAX_GRAMS = {"Aceite de oliva": 30, "Crema de cacahuete": 40, "Almendras": 40,
             "Nueces": 40, "Proteína en polvo (whey)": 60, "Huevo entero": 180}


def macros_for_grams(food: dict, grams: float) -> dict:
    f = grams / 100
    return {k: round(food[k] * f, 1) for k in MACRO_KEYS}


def sum_macros(entries: list) -> dict:
    total = dict.fromkeys(MACRO_KEYS, 0.0)
    for e in entries:
        for k in total:
            total[k] += e.get(k, 0) or 0
    return {k: round(v, 1) for k, v in total.items()}


def _solve_option(option: dict, target: dict, foods_by_name: dict):
    """Grams for p/c/f foods so the meal hits protein, carbs and fat of target."""
    try:
        fixed = [(foods_by_name[n], g) for n, g in option["fixed"]]
        slots = [("protein", foods_by_name[option["p"]]),
                 ("carbs", foods_by_name[option["c"]])]
        if option.get("f"):
            slots.append(("fat", foods_by_name[option["f"]]))
    except KeyError:
        return None  # a food was deleted from the database

    base = sum_macros([macros_for_grams(f, g) for f, g in fixed])
    grams = [0.0] * len(slots)
    for _ in range(25):  # Gauss-Seidel: each food covers "its" macro
        for i, (macro, food) in enumerate(slots):
            other = base[macro] + sum(
                slots[j][1][macro] * grams[j] / 100 for j in range(len(slots)) if j != i)
            need = target[macro] - other
            per_g = food[macro] / 100
            g = need / per_g if per_g > 0 else 0
            grams[i] = min(max(g, 0), MAX_GRAMS.get(food["name"], 400))

    items = [{"food": f, "grams": g} for f, g in fixed]
    items += [{"food": slots[i][1], "grams": grams[i]} for i in range(len(slots))]
    out = []
    for it in items:
        g = round(it["grams"] / 5) * 5
        if g < 5:
            continue
        food = it["food"]
        entry = {"food_id": food["id"], "food_name": food["name"], "grams": g,
                 **macros_for_grams(food, g)}
        if food.get("unit_g"):
            entry["units"] = round(g / food["unit_g"], 1)
            entry["unit_name"] = food.get("unit_name", "ud")
        out.append(entry)
    return out


def _pick(meal_key: str, seed: str, variant: int) -> list:
    options = PLAN_TEMPLATES[meal_key]
    h = int(hashlib.md5(f"{seed}-{meal_key}".encode()).hexdigest(), 16)
    start = (h + variant) % len(options)
    return options[start:] + options[:start]


def build_day_plan(targets: dict, consumed_by_meal: dict, meals: list,
                   foods: dict, seed: str, variant: int = 0) -> dict:
    """Plan for the meals not logged yet today, sized to the remaining macros."""
    foods_by_name = {f["name"]: f for f in foods.values()}
    eaten = sum_macros([m for items in consumed_by_meal.values() for m in items])
    remaining = {k: max(targets[k] - eaten[k], 0) for k in MACRO_KEYS}

    pending = [m for m in meals if not consumed_by_meal.get(m)]
    share_total = sum(MEAL_SHARE[m] for m in pending) or 1

    plan = []
    for m in meals:
        if consumed_by_meal.get(m):
            plan.append({"meal": m, "done": True, "entries": consumed_by_meal[m],
                         "totals": sum_macros(consumed_by_meal[m])})
            continue
        share = MEAL_SHARE[m] / share_total
        target = {k: remaining[k] * share for k in MACRO_KEYS}
        for option in _pick(m, seed, variant):
            items = _solve_option(option, target, foods_by_name)
            if items:
                plan.append({"meal": m, "done": False, "name": option["name"],
                             "entries": items, "target": {k: round(v) for k, v in target.items()},
                             "totals": sum_macros(items)})
                break
    return {"meals": plan, "remaining": {k: round(v) for k, v in remaining.items()},
            "eaten": eaten}

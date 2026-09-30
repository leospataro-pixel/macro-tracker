"""Salud y preferencias: qué alimentos son aptos para cada persona y cuáles prefiere."""

# Tags per food (by name in the food database)
FOOD_TAGS = {
    "Pechuga de pollo (cocida)": {"carne", "ave"},
    "Arroz blanco (cocido)": {"gi_alto"},
    "Huevo entero": {"huevo"},
    "Avena (cruda)": {"gluten"},  # trazas salvo que sea certificada sin gluten
    "Plátano": {"fruta"},
    "Manzana": {"fruta"},
    "Leche entera": {"lacteo", "lactosa", "grasa_saturada"},
    "Yogur natural": {"lacteo", "lactosa"},
    "Pan integral": {"gluten"},
    "Atún en agua (escurrido)": {"pescado"},
    "Salmón (crudo)": {"pescado"},
    "Brócoli (cocido)": {"verdura"},
    "Espinacas (crudas)": {"verdura"},
    "Almendras": {"frutos_secos"},
    "Aceite de oliva": set(),
    "Patata (hervida)": {"gi_alto"},
    "Pasta (cocida)": {"gluten"},
    "Queso fresco 0%": {"lacteo", "lactosa"},
    "Proteína en polvo (whey)": {"lacteo", "lactosa"},
    "Ternera (carne magra)": {"carne", "carne_roja"},
    "Lentejas (cocidas)": {"legumbre"},
    "Aguacate": set(),
    "Naranja": {"fruta"},
    "Nueces": {"frutos_secos"},
    "Tomate": {"verdura"},
    "Pechuga de pavo (fiambre)": {"carne", "ave", "procesado", "sodio_alto"},
    "Claras de huevo": {"huevo"},
    "Queso fresco batido 0%": {"lacteo", "lactosa"},
    "Tortitas de arroz": {"gi_alto"},
    "Merluza (cocida)": {"pescado"},
    "Garbanzos (cocidos)": {"legumbre"},
    "Quinoa (cocida)": set(),
    "Boniato (asado)": set(),
    "Jamón serrano": {"carne", "cerdo", "procesado", "sodio_alto", "grasa_saturada"},
    "Crema de cacahuete": {"frutos_secos"},
    "Ensalada mixta": {"verdura"},
    "Frutos rojos": {"fruta"},
    "Tortilla de trigo (wrap)": {"gluten"},
    "Kiwi": {"fruta"},
    "Arroz integral (cocido)": set(),
    "Lomo de cerdo": {"carne", "cerdo"},
    "Hummus": {"legumbre"},
    "Tofu firme": {"soja"},
    "Soja texturizada (hidratada)": {"soja", "legumbre"},
    "Bebida de soja": {"soja"},
    "Yogur de soja natural": {"soja"},
    "Proteína vegetal en polvo": set(),
    "Pan sin gluten": {"gi_alto"},
    "Leche sin lactosa": {"lacteo"},
    "Gambas (cocidas)": {"marisco"},
    "Edamame": {"soja", "legumbre"},
    "Avena sin gluten (cruda)": set(),
    "Pan de centeno integral": {"gluten"},
}

# name, kcal, protein, carbs, fat, optional unit grams + unit name
EXTRA_FOODS = [
    ("Tofu firme",                   144, 15.7, 3.5,  8.7),
    ("Soja texturizada (hidratada)", 110, 17,   7,    0.4),
    ("Bebida de soja",                33, 3.3,  0.6,  1.8,  250, "vaso"),
    ("Yogur de soja natural",         54, 4.0,  2.5,  3.0,  125, "yogur"),
    ("Proteína vegetal en polvo",    380, 75,   8,    6,    30,  "cacito"),
    ("Pan sin gluten",               245, 4.5,  46,   4.5,  30,  "rebanada"),
    ("Leche sin lactosa",             46, 3.2,  4.8,  1.6,  250, "vaso"),
    ("Gambas (cocidas)",              99, 24,   0.2,  0.3),
    ("Edamame",                      121, 12,   9,    5),
    ("Avena sin gluten (cruda)",     375, 13,   63,   7),
    ("Pan de centeno integral",      220, 8.5,  40,   2.5,  30,  "rebanada"),
]

CONDITIONS = {
    "diabetes":     {"label": "Diabetes / resistencia a la insulina", "emoji": "🩸",
                     "exclude": {"gi_alto"},
                     "tip": "Priorizamos carbohidratos de absorción lenta (legumbres, integrales, "
                            "quinoa, boniato) y limitamos los carbohidratos al 40 % de las calorías."},
    "celiaquia":    {"label": "Celiaquía / sin gluten", "emoji": "🌾",
                     "exclude": {"gluten"},
                     "tip": "Sin pan, pasta ni avena normales. Usa versiones certificadas sin gluten."},
    "lactosa":      {"label": "Intolerancia a la lactosa", "emoji": "🥛",
                     "exclude": {"lactosa"},
                     "tip": "Usamos leche sin lactosa, soja y proteínas sin lácteos."},
    "hipertension": {"label": "Hipertensión", "emoji": "❤️",
                     "exclude": {"sodio_alto"},
                     "tip": "Evitamos embutidos y alimentos muy salados."},
    "colesterol":   {"label": "Colesterol alto", "emoji": "🫀",
                     "exclude": {"procesado", "grasa_saturada"},
                     "tip": "Menos grasa saturada y procesados; más pescado, legumbres y aceite de oliva."},
    "frutos_secos": {"label": "Alergia a frutos secos", "emoji": "🥜",
                     "exclude": {"frutos_secos"}, "tip": "Sin frutos secos ni cremas de cacahuete."},
    "pescado":      {"label": "Alergia a pescado / marisco", "emoji": "🐟",
                     "exclude": {"pescado", "marisco"}, "tip": "Sin pescado ni marisco."},
    "huevo":        {"label": "Alergia al huevo", "emoji": "🥚",
                     "exclude": {"huevo"}, "tip": "Sin huevo ni claras."},
    "vegetariano":  {"label": "Vegetariano", "emoji": "🥗",
                     "exclude": {"carne", "pescado", "marisco"},
                     "tip": "Proteína de huevo, lácteos, legumbres, tofu y soja."},
    "vegano":       {"label": "Vegano", "emoji": "🌱",
                     "exclude": {"carne", "pescado", "marisco", "huevo", "lacteo"},
                     "tip": "Proteína de legumbres, tofu, soja y proteína vegetal."},
}

# "Lo que no como" — whole groups
DISLIKE_GROUPS = {
    "pescado": "🐟 Pescado", "marisco": "🦐 Marisco", "carne_roja": "🥩 Carne roja",
    "cerdo": "🐖 Cerdo", "ave": "🍗 Pollo / pavo", "huevo": "🥚 Huevo",
    "lacteo": "🧀 Lácteos", "legumbre": "🫘 Legumbres", "frutos_secos": "🥜 Frutos secos",
    "soja": "🫛 Soja / tofu",
}

# Candidate foods per plan role, in rough order of how typical they are
POOLS = {
    "desayuno": {
        "protein": ["Queso fresco batido 0%", "Proteína en polvo (whey)", "Claras de huevo",
                    "Pechuga de pavo (fiambre)", "Huevo entero", "Yogur de soja natural",
                    "Proteína vegetal en polvo", "Tofu firme"],
        "carbs":   ["Avena (cruda)", "Pan integral", "Avena sin gluten (cruda)",
                    "Pan de centeno integral", "Pan sin gluten", "Tortitas de arroz",
                    "Boniato (asado)", "Plátano", "Manzana"],
        "fat":     ["Crema de cacahuete", "Aguacate", "Nueces", "Almendras", "Aceite de oliva"],
        "fruit":   ["Plátano", "Frutos rojos", "Kiwi", "Manzana", "Naranja"],
    },
    "snack": {
        "protein": ["Queso fresco batido 0%", "Yogur natural", "Proteína en polvo (whey)",
                    "Pechuga de pavo (fiambre)", "Yogur de soja natural", "Jamón serrano",
                    "Proteína vegetal en polvo", "Edamame"],
        "carbs":   ["Plátano", "Manzana", "Kiwi", "Frutos rojos", "Naranja", "Tortitas de arroz",
                    "Pan integral", "Pan sin gluten"],
        "fat":     ["Nueces", "Almendras", "Crema de cacahuete", "Aguacate"],
    },
    "principal": {
        "protein": ["Pechuga de pollo (cocida)", "Merluza (cocida)", "Salmón (crudo)",
                    "Ternera (carne magra)", "Atún en agua (escurrido)", "Lomo de cerdo",
                    "Gambas (cocidas)", "Huevo entero", "Tofu firme",
                    "Soja texturizada (hidratada)"],
        "carbs":   ["Arroz blanco (cocido)", "Patata (hervida)", "Boniato (asado)",
                    "Arroz integral (cocido)", "Pasta (cocida)", "Quinoa (cocida)",
                    "Lentejas (cocidas)", "Garbanzos (cocidos)", "Pan integral",
                    "Tortilla de trigo (wrap)", "Pan sin gluten"],
        "fat":     ["Aceite de oliva", "Aguacate"],
        "veg":     ["Brócoli (cocido)", "Ensalada mixta", "Espinacas (crudas)", "Tomate"],
    },
}
MEAL_POOL = {"desayuno": "desayuno", "almuerzo": "snack", "merienda": "snack",
             "comida": "principal", "cena": "principal"}
FIXED_GRAMS = {"fruit": 120, "veg": 150}
ROLE_LABELS = {"protein": "Proteína", "carbs": "Carbohidrato", "fat": "Grasa",
               "fruit": "Fruta", "veg": "Verdura"}


def tags(name: str) -> set:
    return FOOD_TAGS.get(name, set())


def blocked_reason(name: str, prefs: dict) -> str | None:
    """Why this food can't be recommended to this person (None = allowed)."""
    t = tags(name)
    for c in prefs.get("conditions", []):
        if CONDITIONS.get(c) and t & CONDITIONS[c]["exclude"]:
            return CONDITIONS[c]["label"]
    for g in prefs.get("dislike_groups", []):
        if g in t:
            return "No comes " + DISLIKE_GROUPS.get(g, g).split(" ", 1)[-1].lower()
    if name in prefs.get("dislikes", []):
        return "No te gusta"
    return None


def health_blocked(name: str, prefs: dict) -> str | None:
    """Only medical / diet conditions (used to warn when logging)."""
    t = tags(name)
    for c in prefs.get("conditions", []):
        if CONDITIONS.get(c) and t & CONDITIONS[c]["exclude"]:
            return CONDITIONS[c]["label"]
    return None


def candidates(meal: str, role: str, prefs: dict, available: set) -> list:
    """Allowed foods for a role: liked ones first, then the rest (pool order)."""
    pool = POOLS[MEAL_POOL[meal]].get(role, [])
    ok = [n for n in pool if n in available and not blocked_reason(n, prefs)]
    likes = set(prefs.get("likes", []))
    return [n for n in ok if n in likes] + [n for n in ok if n not in likes]


def pref_foods(available: set) -> dict:
    """Foods shown in the 'what do you like' picker, grouped by role."""
    names = {"protein": "Proteínas", "carbs": "Carbohidratos", "fat": "Grasas"}
    groups = {v: [] for v in names.values()} | {"Frutas y verduras": []}
    seen = set()
    for pool in POOLS.values():
        for role, foods in pool.items():
            for n in foods:
                if n in available and n not in seen:
                    seen.add(n)
                    fv = tags(n) & {"fruta", "verdura"} or role in ("fruit", "veg")
                    groups["Frutas y verduras" if fv else names[role]].append(n)
    return groups


def adjust_targets(targets: dict, conditions: list) -> dict:
    """Diabetes: carbs capped at 40 % of kcal, the rest moved to fat."""
    t = dict(targets)
    if "diabetes" in conditions:
        max_carbs = round(t["calories"] * 0.40 / 4)
        if t["carbs"] > max_carbs:
            extra_kcal = (t["carbs"] - max_carbs) * 4
            t["carbs"] = max_carbs
            t["fat"] = round(t["fat"] + extra_kcal / 9)
    return t

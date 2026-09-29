"""Biblioteca de rutinas de entrenamiento y recomendaciones según objetivo."""

GOALS = {
    "lose":     {"label": "Perder grasa",     "emoji": "🔥"},
    "maintain": {"label": "Mantenimiento",    "emoji": "⚖️"},
    "recomp":   {"label": "Recomposición",    "emoji": "🔄"},
    "gain":     {"label": "Ganar músculo",    "emoji": "💪"},
}

LEVELS = {"beginner": "Principiante", "intermediate": "Intermedio", "advanced": "Avanzado"}


def ex(name, sets, reps, rest="90s"):
    return {"name": name, "sets": sets, "reps": reps, "rest": rest}


ROUTINES = [
    {
        "id": "fullbody3",
        "name": "Full Body 3 días",
        "goals": ["recomp", "maintain", "lose", "gain"],
        "level": "beginner",
        "days_per_week": 3,
        "equipment": "Gimnasio",
        "description": "Todo el cuerpo en cada sesión. Ideal para empezar o volver "
                       "a entrenar: mucha frecuencia por grupo muscular y poco tiempo.",
        "cardio": "2 sesiones de 20-30 min de caminata rápida o bici suave en días libres.",
        "days": [
            {"name": "Full Body A", "exercises": [
                ex("Sentadilla", 3, "8-10", "2min"),
                ex("Press banca", 3, "8-10", "2min"),
                ex("Remo con barra", 3, "8-10"),
                ex("Press militar mancuernas", 2, "10-12"),
                ex("Curl bíceps", 2, "12-15", "60s"),
                ex("Plancha", 3, "30-45s", "60s"),
            ]},
            {"name": "Full Body B", "exercises": [
                ex("Peso muerto rumano", 3, "8-10", "2min"),
                ex("Press inclinado mancuernas", 3, "10-12"),
                ex("Jalón al pecho", 3, "10-12"),
                ex("Zancadas", 2, "10/pierna"),
                ex("Extensión tríceps polea", 2, "12-15", "60s"),
                ex("Elevación de piernas colgado", 3, "10-12", "60s"),
            ]},
            {"name": "Full Body C", "exercises": [
                ex("Prensa de piernas", 3, "10-12", "2min"),
                ex("Fondos o press cerrado", 3, "8-10"),
                ex("Remo en polea baja", 3, "10-12"),
                ex("Elevaciones laterales", 3, "12-15", "60s"),
                ex("Curl femoral", 2, "12-15", "60s"),
                ex("Rueda abdominal", 3, "8-12", "60s"),
            ]},
        ],
    },
    {
        "id": "upperlower4",
        "name": "Torso / Pierna 4 días",
        "goals": ["gain", "recomp"],
        "level": "intermediate",
        "days_per_week": 4,
        "equipment": "Gimnasio",
        "description": "Cada grupo muscular 2 veces por semana con más volumen. "
                       "La mejor relación resultado/tiempo para ganar músculo.",
        "cardio": "Opcional: 2 x 20 min de cardio suave para salud cardiovascular.",
        "days": [
            {"name": "Torso fuerza", "exercises": [
                ex("Press banca", 4, "5-6", "3min"),
                ex("Remo con barra", 4, "6-8", "2min"),
                ex("Press militar", 3, "6-8", "2min"),
                ex("Dominadas", 3, "6-10", "2min"),
                ex("Curl bíceps barra", 2, "8-10", "90s"),
                ex("Press francés", 2, "8-10", "90s"),
            ]},
            {"name": "Pierna fuerza", "exercises": [
                ex("Sentadilla", 4, "5-6", "3min"),
                ex("Peso muerto rumano", 3, "6-8", "2min"),
                ex("Prensa de piernas", 3, "8-10", "2min"),
                ex("Curl femoral", 3, "10-12", "90s"),
                ex("Elevación de gemelos", 4, "10-15", "60s"),
            ]},
            {"name": "Torso hipertrofia", "exercises": [
                ex("Press inclinado mancuernas", 3, "10-12"),
                ex("Jalón al pecho", 3, "10-12"),
                ex("Aperturas en polea", 3, "12-15", "60s"),
                ex("Remo con mancuerna", 3, "10-12"),
                ex("Elevaciones laterales", 4, "12-15", "60s"),
                ex("Curl martillo", 3, "10-12", "60s"),
                ex("Extensión tríceps polea", 3, "12-15", "60s"),
            ]},
            {"name": "Pierna hipertrofia", "exercises": [
                ex("Sentadilla búlgara", 3, "10/pierna"),
                ex("Hip thrust", 3, "10-12"),
                ex("Extensión de cuádriceps", 3, "12-15", "60s"),
                ex("Curl femoral sentado", 3, "12-15", "60s"),
                ex("Elevación de gemelos", 4, "12-15", "60s"),
                ex("Plancha", 3, "45-60s", "60s"),
            ]},
        ],
    },
    {
        "id": "ppl6",
        "name": "Push / Pull / Legs",
        "goals": ["gain"],
        "level": "advanced",
        "days_per_week": 6,
        "equipment": "Gimnasio",
        "description": "Empuje, tirón y pierna (3 o 6 días). Máximo volumen para "
                       "quien ya lleva tiempo entrenando y quiere seguir creciendo.",
        "cardio": "Caminar 8.000-10.000 pasos diarios es suficiente.",
        "days": [
            {"name": "Push (empuje)", "exercises": [
                ex("Press banca", 4, "6-8", "2min"),
                ex("Press militar", 3, "8-10", "2min"),
                ex("Press inclinado mancuernas", 3, "10-12"),
                ex("Elevaciones laterales", 4, "12-15", "60s"),
                ex("Fondos", 3, "8-12"),
                ex("Extensión tríceps polea", 3, "12-15", "60s"),
            ]},
            {"name": "Pull (tirón)", "exercises": [
                ex("Dominadas lastradas", 4, "6-8", "2min"),
                ex("Remo con barra", 3, "8-10", "2min"),
                ex("Remo en polea baja", 3, "10-12"),
                ex("Face pull", 3, "15-20", "60s"),
                ex("Curl bíceps barra", 3, "8-10", "60s"),
                ex("Curl martillo", 2, "10-12", "60s"),
            ]},
            {"name": "Legs (pierna)", "exercises": [
                ex("Sentadilla", 4, "6-8", "3min"),
                ex("Peso muerto rumano", 3, "8-10", "2min"),
                ex("Prensa de piernas", 3, "10-12", "2min"),
                ex("Curl femoral", 3, "10-12", "60s"),
                ex("Extensión de cuádriceps", 3, "12-15", "60s"),
                ex("Elevación de gemelos", 4, "10-15", "60s"),
            ]},
        ],
    },
    {
        "id": "fatloss4",
        "name": "Quema grasa: fuerza + HIIT",
        "goals": ["lose"],
        "level": "intermediate",
        "days_per_week": 4,
        "equipment": "Gimnasio",
        "description": "Fuerza para mantener el músculo mientras estás en déficit, "
                       "más circuitos metabólicos y HIIT para gastar más calorías.",
        "cardio": "Objetivo diario: 8.000-10.000 pasos. Es lo que más suma al déficit.",
        "days": [
            {"name": "Fuerza tren superior", "exercises": [
                ex("Press banca", 3, "6-8", "2min"),
                ex("Remo con barra", 3, "6-8", "2min"),
                ex("Press militar mancuernas", 3, "8-10"),
                ex("Jalón al pecho", 3, "10-12"),
                ex("Superserie curl + tríceps", 3, "12+12", "60s"),
            ]},
            {"name": "Circuito metabólico + HIIT", "exercises": [
                ex("Kettlebell swing", 4, "15", "30s"),
                ex("Burpees", 4, "10", "30s"),
                ex("Goblet squat", 4, "15", "30s"),
                ex("Mountain climbers", 4, "30s", "30s"),
                ex("HIIT bici: 30s fuerte / 60s suave", 8, "rondas", "-"),
            ]},
            {"name": "Fuerza tren inferior", "exercises": [
                ex("Sentadilla", 3, "6-8", "2min"),
                ex("Peso muerto rumano", 3, "8-10", "2min"),
                ex("Zancadas caminando", 3, "12/pierna"),
                ex("Hip thrust", 3, "10-12"),
                ex("Plancha lateral", 3, "30s/lado", "45s"),
            ]},
            {"name": "Cardio LISS + core", "exercises": [
                ex("Caminata en cinta inclinada", 1, "35-45 min", "-"),
                ex("Crunch en polea", 3, "12-15", "45s"),
                ex("Rueda abdominal", 3, "8-12", "45s"),
                ex("Pallof press", 3, "12/lado", "45s"),
            ]},
        ],
    },
    {
        "id": "home3",
        "name": "En casa sin material",
        "goals": ["lose", "maintain", "recomp"],
        "level": "beginner",
        "days_per_week": 3,
        "equipment": "Casa (sin material)",
        "description": "Peso corporal, 30-40 minutos. Perfecto para toda la familia "
                       "o cuando no hay tiempo de ir al gimnasio.",
        "cardio": "Paseos diarios de 30 min o 8.000 pasos.",
        "days": [
            {"name": "Casa A", "exercises": [
                ex("Sentadilla con peso corporal", 4, "15-20", "60s"),
                ex("Flexiones (rodillas si hace falta)", 4, "8-15", "60s"),
                ex("Remo invertido en mesa", 3, "8-12", "60s"),
                ex("Puente de glúteo", 3, "15-20", "45s"),
                ex("Plancha", 3, "30-45s", "45s"),
            ]},
            {"name": "Casa B (circuito)", "exercises": [
                ex("Jumping jacks", 4, "40s", "20s"),
                ex("Zancadas alternas", 4, "12/pierna", "30s"),
                ex("Flexiones pica", 4, "8-10", "30s"),
                ex("Burpees", 4, "8-10", "30s"),
                ex("Mountain climbers", 4, "30s", "30s"),
            ]},
            {"name": "Casa C", "exercises": [
                ex("Sentadilla búlgara en silla", 3, "10/pierna", "60s"),
                ex("Fondos en silla", 3, "10-15", "60s"),
                ex("Superman", 3, "12-15", "45s"),
                ex("Peso muerto a una pierna", 3, "10/pierna", "45s"),
                ex("Crunch bicicleta", 3, "20", "45s"),
            ]},
        ],
    },
]

ROUTINES_BY_ID = {r["id"]: r for r in ROUTINES}

GOAL_TIPS = {
    "lose": [
        "Déficit moderado (~20%): pierdes grasa sin perder músculo.",
        "Mantén la fuerza: entrena pesado 2-3 días aunque estés a dieta.",
        "Proteína alta (≈2 g/kg) para conservar músculo y controlar el hambre.",
        "Los pasos diarios (8-10k) queman más que una sesión de cardio.",
    ],
    "gain": [
        "Superávit ligero (~10%): ganas músculo con poca grasa.",
        "Sube peso o repeticiones cada semana (sobrecarga progresiva).",
        "Duerme 7-9 h: el músculo se construye descansando.",
        "Proteína ≈1,8-2 g/kg repartida en 3-5 comidas.",
    ],
    "recomp": [
        "Come en mantenimiento y entrena fuerza con constancia.",
        "Prioriza la proteína (≈2 g/kg) todos los días.",
        "Funciona mejor si eres principiante o vuelves a entrenar.",
    ],
    "maintain": [
        "Mantén calorías estables y 3 días de fuerza por semana.",
        "Controla el peso semanal; si sube o baja >1 kg, ajusta 150 kcal.",
    ],
}


def recommended_routines(goal: str, level: str | None = None) -> list:
    """Rutinas ordenadas por encaje con el objetivo (y el nivel si se da)."""
    order = list(LEVELS)

    def score(r):
        s = 0 if goal in r["goals"] else 10
        s += r["goals"].index(goal) if goal in r["goals"] else 0
        if level:
            s += abs(order.index(r["level"]) - order.index(level))
        return s

    return sorted(ROUTINES, key=score)

"""Estiramientos y rutinas guiadas de estiramientos."""

from exercises import slugify


def s(name, img, primary, secondary, hold, steps, per_side=True):
    return {"name": name, "slug": slugify(name), "img": img, "primary": primary,
            "secondary": secondary, "hold": hold, "per_side": per_side, "steps": steps}


STRETCHES = [
    # ── Tren inferior ──
    s("Flexores de cadera de rodillas", "Kneeling Hip Flexor", ["quads"], ["abs", "glutes"], 30,
      ["Rodilla trasera apoyada en una esterilla, pie delantero adelantado.",
       "Mete la pelvis (como si metieras el culo) y aprieta el glúteo de atrás.",
       "Lleva la cadera hacia delante hasta notar tensión delante del muslo trasero."]),
    s("Isquiotibiales de pie", "Standing Hamstring and Calf Stretch", ["hamstrings"], ["calves", "lower_back"], 30,
      ["Adelanta un pie con el talón en el suelo y la punta hacia arriba.",
       "Inclínate desde la cadera con la espalda recta.",
       "Para cuando notes tensión detrás del muslo, sin rebotar."]),
    s("Cuádriceps de pie", "Quad Stretch", ["quads"], [], 30,
      ["De pie, agarra el empeine y lleva el talón al glúteo.",
       "Rodillas juntas y pelvis metida.",
       "Apóyate en una pared si pierdes el equilibrio."]),
    s("Glúteo tumbado (rodilla al pecho)", "Lying Glute", ["glutes"], ["lower_back"], 30,
      ["Tumbado boca arriba, lleva una rodilla hacia el hombro contrario.",
       "Tira suavemente con las manos.",
       "Mantén la espalda y la cabeza apoyadas."]),
    s("Figura 4 sentado", "Seated Glute", ["glutes"], ["lower_back"], 30,
      ["Sentado, cruza un tobillo sobre la rodilla contraria.",
       "Inclínate hacia delante con la espalda recta.",
       "Notarás el estiramiento en el glúteo de la pierna cruzada."]),
    s("Aductores (mariposa)", "Groin and Back Stretch", ["adductors"], ["lower_back"], 40,
      ["Sentado, junta las plantas de los pies y acércalas a la ingle.",
       "Deja caer las rodillas hacia el suelo.",
       "Inclínate hacia delante con la espalda recta."], per_side=False),
    s("Gemelos en la pared", "Calf Stretch Hands Against Wall", ["calves"], [], 30,
      ["Manos en la pared, una pierna atrás estirada.",
       "Talón trasero pegado al suelo y punta al frente.",
       "Lleva la cadera hacia la pared hasta notar tensión en la pantorrilla."]),
    # ── Tren superior ──
    s("Pecho y hombro", "Chest And Front Of Shoulder Stretch", ["chest"], ["front_delts", "biceps"], 30,
      ["Apoya el antebrazo en el marco de una puerta a la altura del hombro.",
       "Gira el cuerpo hacia el lado contrario.",
       "Notarás el estiramiento en el pecho y la parte delantera del hombro."]),
    s("Dorsal por encima de la cabeza", "Overhead Lat", ["lats"], ["obliques", "triceps"], 30,
      ["De pie, sube un brazo por encima de la cabeza.",
       "Agarra la muñeca con la otra mano.",
       "Inclínate hacia el lado contrario sin girar el tronco."]),
    s("Hombro cruzado", "Shoulder Stretch", ["rear_delts"], ["traps"], 30,
      ["Cruza un brazo estirado por delante del pecho.",
       "Con la otra mano, empuja el codo hacia ti.",
       "Mantén el hombro bajo, lejos de la oreja."]),
    s("Tríceps", "Triceps Stretch", ["triceps"], ["lats"], 30,
      ["Sube un brazo y dobla el codo detrás de la cabeza.",
       "Con la otra mano, empuja suavemente el codo hacia abajo.",
       "Espalda recta y abdomen activo."]),
    # ── Espalda y movilidad ──
    s("Postura del niño", "Child's Pose", ["lower_back"], ["lats", "glutes"], 40,
      ["De rodillas, siéntate sobre los talones.",
       "Estira los brazos al frente y apoya la frente en el suelo.",
       "Respira hondo y relaja la espalda."], per_side=False),
    s("Gato-vaca", "Cat Stretch", ["lower_back"], ["abs", "traps"], 40,
      ["A cuatro patas, manos bajo los hombros y rodillas bajo la cadera.",
       "Redondea la espalda mirando al ombligo (gato).",
       "Luego arquéala mirando al frente (vaca). Alterna despacio."], per_side=False),
    s("El mejor estiramiento del mundo", "World's Greatest Stretch",
      ["hamstrings", "quads", "glutes"], ["adductors", "obliques", "traps"], 30,
      ["Desde zancada, apoya las manos por dentro del pie delantero.",
       "Lleva el codo hacia el tobillo delantero.",
       "Gira el tronco abriendo el brazo hacia el techo."]),
]

BY_SLUG = {x["slug"]: x for x in STRETCHES}

ROUTINES = [
    {"id": "inferior", "name": "Tren inferior", "emoji": "🦵",
     "description": "Después de entrenar pierna o de correr.",
     "items": ["flexores-de-cadera-de-rodillas", "isquiotibiales-de-pie", "cuadriceps-de-pie",
               "gluteo-tumbado-rodilla-al-pecho", "aductores-mariposa", "gemelos-en-la-pared"]},
    {"id": "superior", "name": "Tren superior", "emoji": "💪",
     "description": "Después de pecho, espalda, hombros o brazos.",
     "items": ["pecho-y-hombro", "dorsal-por-encima-de-la-cabeza", "hombro-cruzado",
               "triceps", "postura-del-nino"]},
    {"id": "espalda", "name": "Espalda y movilidad", "emoji": "🧘",
     "description": "Por la mañana o tras muchas horas de pie o sentado.",
     "items": ["gato-vaca", "postura-del-nino", "el-mejor-estiramiento-del-mundo",
               "figura-4-sentado", "flexores-de-cadera-de-rodillas"]},
]
ROUTINES_BY_ID = {r["id"]: r for r in ROUTINES}


def routine_steps(routine: dict) -> list:
    """Expand a routine into timed steps (one per side when needed)."""
    steps = []
    for slug in routine["items"]:
        st = BY_SLUG[slug]
        sides = ["Lado izquierdo", "Lado derecho"] if st["per_side"] else [""]
        for side in sides:
            steps.append({**st, "side": side})
    return steps


def routine_minutes(routine: dict) -> int:
    secs = sum(x["hold"] + 5 for x in routine_steps(routine))
    return max(1, round(secs / 60))

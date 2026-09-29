"""Ficha de cada ejercicio: músculos implicados y técnica correcta."""

import re
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus

MUSCLES = {
    "chest":       "Pecho",
    "front_delts": "Hombro anterior",
    "side_delts":  "Hombro lateral",
    "rear_delts":  "Hombro posterior",
    "biceps":      "Bíceps",
    "triceps":     "Tríceps",
    "forearms":    "Antebrazos",
    "abs":         "Abdomen",
    "obliques":    "Oblicuos",
    "traps":       "Trapecio / espalda alta",
    "lats":        "Dorsales",
    "lower_back":  "Lumbares",
    "glutes":      "Glúteos",
    "quads":       "Cuádriceps",
    "hamstrings":  "Isquiotibiales",
    "adductors":   "Aductores",
    "calves":      "Gemelos",
}

# Grouping for the exercise library filter
MUSCLE_GROUPS = {
    "Pecho": ["chest"],
    "Espalda": ["lats", "traps", "lower_back"],
    "Hombros": ["front_delts", "side_delts", "rear_delts"],
    "Brazos": ["biceps", "triceps", "forearms"],
    "Core": ["abs", "obliques"],
    "Pierna": ["quads", "hamstrings", "glutes", "adductors", "calves"],
}


def e(primary, secondary, steps, mistakes, video=None):
    return {"primary": primary, "secondary": secondary, "steps": steps,
            "mistakes": mistakes, "video": video}


EXERCISES = {
    # ── Pecho ──
    "Press banca": e(
        ["chest"], ["front_delts", "triceps"],
        ["Túmbate con los ojos bajo la barra y los pies firmes en el suelo.",
         "Junta las escápulas y saca pecho: mantén un ligero arco lumbar.",
         "Baja la barra controlada hasta la parte baja del pecho, codos a ~45°.",
         "Empuja hacia arriba y ligeramente hacia la cara sin despegar los glúteos."],
        ["Abrir los codos a 90° (sobrecarga el hombro).", "Rebotar la barra en el pecho."]),
    "Press inclinado mancuernas": e(
        ["chest"], ["front_delts", "triceps"],
        ["Banco a 30-45°. Mancuernas a la altura del pecho, palmas al frente.",
         "Escápulas atrás y abajo durante todo el movimiento.",
         "Empuja hacia arriba juntando ligeramente las mancuernas arriba.",
         "Baja lento hasta notar estiramiento en el pecho."],
        ["Banco demasiado inclinado (trabaja más hombro).", "Chocar las mancuernas arriba."]),
    "Aperturas en polea": e(
        ["chest"], ["front_delts"],
        ["Poleas a la altura del pecho, un paso adelante y tronco algo inclinado.",
         "Codos ligeramente flexionados y fijos.",
         "Cierra los brazos en arco hasta juntar las manos delante del pecho.",
         "Vuelve despacio hasta notar el estiramiento."],
        ["Flexionar y extender los codos (se convierte en un press).", "Usar demasiado peso."]),
    "Flexiones (rodillas si hace falta)": e(
        ["chest"], ["triceps", "front_delts", "abs"],
        ["Manos algo más abiertas que los hombros, cuerpo en línea recta.",
         "Aprieta glúteos y abdomen para no hundir la cadera.",
         "Baja hasta casi tocar el suelo con el pecho, codos a ~45°.",
         "Empuja el suelo hasta estirar los brazos."],
        ["Cadera caída o en pico.", "Recorrido a medias."]),
    "Fondos": e(
        ["chest", "triceps"], ["front_delts"],
        ["Agárrate a las paralelas con brazos estirados y hombros abajo.",
         "Inclina un poco el tronco hacia delante (más pecho).",
         "Baja hasta que los codos formen 90°.",
         "Sube empujando sin bloquear del todo los codos."],
        ["Bajar demasiado (estrés en el hombro).", "Encoger los hombros hacia las orejas."]),

    # ── Espalda ──
    "Dominadas": e(
        ["lats"], ["biceps", "traps", "rear_delts", "forearms"],
        ["Agarre prono algo más ancho que los hombros, cuerpo colgado.",
         "Empieza bajando las escápulas (sin doblar codos).",
         "Tira llevando los codos hacia las costillas hasta pasar la barbilla.",
         "Baja controlado hasta estirar los brazos."],
        ["Balancearse o hacer kipping.", "Medias repeticiones sin estirar abajo."]),
    "Jalón al pecho": e(
        ["lats"], ["biceps", "traps", "rear_delts"],
        ["Siéntate con los muslos bien sujetos, agarre algo más ancho que los hombros.",
         "Pecho arriba e inclinación ligera hacia atrás.",
         "Tira de la barra hacia la parte alta del pecho llevando los codos abajo.",
         "Sube despacio dejando que los dorsales se estiren."],
        ["Tirar detrás de la nuca.", "Echarse muy atrás usando el impulso."]),
    "Remo con barra": e(
        ["lats", "traps"], ["rear_delts", "biceps", "lower_back"],
        ["Pies a la anchura de caderas, bisagra de cadera hasta ~45° de tronco.",
         "Espalda neutra, abdomen apretado, barra colgando bajo los hombros.",
         "Tira de la barra hacia el ombligo llevando los codos atrás.",
         "Baja controlado sin perder la postura."],
        ["Redondear la espalda.", "Levantar el tronco para mover más peso."]),
    "Remo con mancuerna": e(
        ["lats"], ["traps", "rear_delts", "biceps"],
        ["Apoya rodilla y mano en el banco, espalda plana.",
         "Mancuerna colgando, hombro abajo.",
         "Tira llevando el codo hacia la cadera, pegado al cuerpo.",
         "Baja hasta estirar el brazo por completo."],
        ["Girar el tronco para subir el peso.", "Tirar con el bíceps en vez de con el codo."]),
    "Remo en polea baja": e(
        ["lats", "traps"], ["rear_delts", "biceps"],
        ["Siéntate con rodillas algo flexionadas y espalda recta.",
         "Tira del agarre hacia el abdomen juntando escápulas.",
         "Pausa un segundo con el pecho alto.",
         "Estira los brazos dejando que los hombros vayan adelante sin encorvarte."],
        ["Balancear el tronco adelante y atrás.", "Encoger los hombros."]),
    "Remo invertido en mesa": e(
        ["lats", "traps"], ["biceps", "rear_delts", "abs"],
        ["Túmbate bajo una mesa firme y agarra el borde.",
         "Cuerpo recto de talones a cabeza.",
         "Tira del pecho hacia la mesa juntando escápulas.",
         "Baja controlado."],
        ["Usar una mesa inestable.", "Dejar caer la cadera."]),
    "Face pull": e(
        ["rear_delts"], ["traps", "side_delts"],
        ["Polea a la altura de la cara, cuerda con agarre neutro.",
         "Tira hacia la cara separando las manos a los lados de las orejas.",
         "Codos altos y rotación externa al final.",
         "Vuelve lento."],
        ["Usar demasiado peso.", "Tirar hacia el cuello con codos bajos."]),
    "Peso muerto rumano": e(
        ["hamstrings", "glutes"], ["lower_back", "forearms"],
        ["De pie con la barra a la altura de las caderas, rodillas ligeramente flexionadas.",
         "Lleva la cadera atrás deslizando la barra pegada a los muslos.",
         "Baja hasta notar tensión en los isquios (media tibia aprox.).",
         "Sube empujando la cadera hacia delante y aprieta glúteos."],
        ["Redondear la espalda.", "Convertirlo en una sentadilla doblando mucho las rodillas."]),
    "Superman": e(
        ["lower_back"], ["glutes", "traps"],
        ["Túmbate boca abajo con brazos estirados al frente.",
         "Eleva a la vez brazos, pecho y piernas unos centímetros.",
         "Aguanta 1-2 segundos arriba.",
         "Baja despacio."],
        ["Hiperextender el cuello mirando al frente.", "Hacerlo rápido y con impulso."]),

    # ── Hombros ──
    "Press militar": e(
        ["front_delts", "side_delts"], ["triceps", "traps", "abs"],
        ["De pie, barra apoyada en la parte alta del pecho, agarre algo más ancho que los hombros.",
         "Aprieta glúteos y abdomen.",
         "Empuja la barra en línea recta apartando la cara y mete la cabeza al pasar.",
         "Baja controlado hasta la clavícula."],
        ["Arquear mucho la zona lumbar.", "Empujar la barra hacia delante en vez de vertical."]),
    "Elevaciones laterales": e(
        ["side_delts"], ["traps", "front_delts"],
        ["De pie, mancuernas a los lados, codos algo flexionados.",
         "Sube los brazos a los lados hasta la altura de los hombros.",
         "Lidera con los codos, no con las manos.",
         "Baja lento en 2-3 segundos."],
        ["Balancear el cuerpo.", "Subir por encima de los hombros encogiendo el trapecio."]),
    "Flexiones pica": e(
        ["front_delts", "side_delts"], ["triceps", "traps"],
        ["Posición de V invertida: caderas altas, manos y pies en el suelo.",
         "Baja la cabeza hacia el suelo entre las manos flexionando codos.",
         "Empuja hasta estirar los brazos.",
         "Mantén las caderas altas todo el rato."],
        ["Abrir mucho los codos.", "Bajar las caderas (se convierte en flexión normal)."]),

    # ── Brazos ──
    "Curl bíceps": e(
        ["biceps"], ["forearms"],
        ["De pie, codos pegados al cuerpo, palmas al frente.",
         "Sube el peso flexionando solo el codo.",
         "Aprieta arriba un segundo.",
         "Baja despacio hasta estirar el brazo."],
        ["Balancear el tronco.", "Adelantar los codos."]),
    "Curl martillo": e(
        ["biceps", "forearms"], [],
        ["Mancuernas con agarre neutro (palmas enfrentadas).",
         "Codos pegados, sube hasta el hombro.",
         "Baja controlado."],
        ["Girar la muñeca.", "Usar impulso."]),
    "Extensión tríceps polea": e(
        ["triceps"], [],
        ["De pie frente a la polea alta, codos pegados al cuerpo.",
         "Extiende los codos hasta estirar los brazos.",
         "Separa un poco la cuerda al final.",
         "Sube sin mover los codos de sitio."],
        ["Mover los hombros y los codos.", "Inclinarse encima del peso."]),
    "Press francés": e(
        ["triceps"], [],
        ["Tumbado, barra Z sobre la frente con brazos verticales.",
         "Baja flexionando solo los codos hacia la frente.",
         "Extiende hasta volver arriba.",
         "Codos apuntando al techo todo el tiempo."],
        ["Abrir los codos.", "Mover los hombros (se convierte en un press)."]),
    "Fondos en silla": e(
        ["triceps"], ["chest", "front_delts"],
        ["Manos en el borde de una silla estable, piernas al frente.",
         "Baja doblando codos hacia atrás hasta 90°.",
         "Empuja hasta estirar los brazos.",
         "Espalda cerca de la silla."],
        ["Bajar demasiado.", "Abrir los codos hacia fuera."]),

    # ── Piernas ──
    "Sentadilla": e(
        ["quads", "glutes"], ["adductors", "hamstrings", "lower_back", "abs"],
        ["Barra sobre el trapecio, pies a la anchura de hombros y puntas algo abiertas.",
         "Coge aire, aprieta abdomen y baja llevando la cadera atrás y abajo.",
         "Rodillas en la dirección de las puntas; baja al menos hasta paralelo.",
         "Sube empujando el suelo con todo el pie, pecho arriba."],
        ["Rodillas hacia dentro.", "Levantar los talones o redondear la espalda."]),
    "Goblet squat": e(
        ["quads", "glutes"], ["adductors", "abs"],
        ["Sujeta una kettlebell o mancuerna pegada al pecho.",
         "Baja entre las piernas manteniendo el tronco erguido.",
         "Codos por dentro de las rodillas abajo.",
         "Sube empujando con todo el pie."],
        ["Inclinarse hacia delante.", "Rodillas hacia dentro."]),
    "Prensa de piernas": e(
        ["quads", "glutes"], ["adductors", "hamstrings"],
        ["Espalda y cadera bien apoyadas, pies a la anchura de hombros.",
         "Baja hasta que las rodillas formen ~90°.",
         "Empuja con todo el pie sin bloquear las rodillas arriba.",
         "No despegues la zona lumbar del respaldo."],
        ["Bajar tanto que se levante la cadera.", "Bloquear las rodillas."]),
    "Extensión de cuádriceps": e(
        ["quads"], [],
        ["Rodilla alineada con el eje de la máquina.",
         "Extiende las piernas hasta arriba y aprieta 1 segundo.",
         "Baja lento."],
        ["Dar patadas con impulso.", "Levantar la cadera del asiento."]),
    "Curl femoral": e(
        ["hamstrings"], ["calves"],
        ["Tumbado, rodillas justo fuera del banco, rodillo sobre los tobillos.",
         "Flexiona llevando los talones al glúteo.",
         "Baja despacio sin dejar caer el peso."],
        ["Levantar la cadera.", "Recorrido corto."]),
    "Zancadas": e(
        ["quads", "glutes"], ["hamstrings", "adductors", "calves"],
        ["Da un paso largo al frente.",
         "Baja hasta que ambas rodillas formen ~90°; la de atrás casi toca el suelo.",
         "Tronco erguido, rodilla delantera sobre el pie.",
         "Empuja con el talón delantero para volver."],
        ["Paso demasiado corto (la rodilla pasa mucho la punta).", "Rodilla hacia dentro."]),
    "Sentadilla búlgara": e(
        ["quads", "glutes"], ["hamstrings", "adductors"],
        ["Pie trasero apoyado en un banco, pie delantero adelantado.",
         "Baja en vertical hasta que el muslo delantero quede paralelo.",
         "Tronco algo inclinado para más glúteo.",
         "Sube empujando con el pie delantero."],
        ["Pie delantero demasiado cerca del banco.", "Perder el equilibrio por ir rápido."]),
    "Hip thrust": e(
        ["glutes"], ["hamstrings", "quads"],
        ["Espalda alta apoyada en un banco, barra sobre la cadera (con protector).",
         "Pies a la anchura de caderas, rodillas a 90° arriba.",
         "Empuja la cadera arriba hasta alinear tronco y muslos.",
         "Aprieta glúteos 1 segundo, mentón hacia el pecho."],
        ["Arquear la zona lumbar en vez de extender cadera.", "Pies demasiado lejos."]),
    "Puente de glúteo": e(
        ["glutes"], ["hamstrings", "abs"],
        ["Tumbado boca arriba, rodillas flexionadas, pies en el suelo.",
         "Eleva la cadera apretando glúteos hasta alinear rodillas-cadera-hombros.",
         "Aguanta un segundo y baja."],
        ["Empujar con la zona lumbar.", "Separar las rodillas hacia fuera."]),
    "Peso muerto a una pierna": e(
        ["hamstrings", "glutes"], ["lower_back", "abs"],
        ["De pie sobre una pierna, rodilla ligeramente flexionada.",
         "Inclina el tronco adelante mientras la otra pierna sube atrás.",
         "Espalda recta, cadera nivelada.",
         "Vuelve arriba apretando glúteo."],
        ["Girar la cadera.", "Redondear la espalda."]),
    "Elevación de gemelos": e(
        ["calves"], [],
        ["Puntas de los pies en un escalón, talones fuera.",
         "Sube lo más alto posible y aguanta 1 segundo.",
         "Baja hasta notar el estiramiento."],
        ["Rebotar.", "Recorrido corto."]),

    # ── Core ──
    "Plancha": e(
        ["abs"], ["obliques", "front_delts", "glutes"],
        ["Antebrazos en el suelo bajo los hombros.",
         "Cuerpo recto de cabeza a talones.",
         "Aprieta abdomen y glúteos; respira con normalidad."],
        ["Cadera caída.", "Cadera demasiado alta."]),
    "Plancha lateral": e(
        ["obliques"], ["abs", "glutes", "side_delts"],
        ["Tumbado de lado, antebrazo bajo el hombro.",
         "Eleva la cadera hasta formar una línea recta.",
         "Aguanta sin dejar caer la cadera."],
        ["Rotar el tronco.", "Hundir el hombro."]),
    "Rueda abdominal": e(
        ["abs"], ["lats", "obliques", "front_delts"],
        ["De rodillas, manos en la rueda bajo los hombros.",
         "Rueda hacia delante manteniendo la pelvis metida (retroversión).",
         "Llega hasta donde controles sin arquear la zona lumbar.",
         "Vuelve tirando con el abdomen."],
        ["Arquear la zona lumbar.", "Ir más lejos de lo que controlas."]),
    "Elevación de piernas colgado": e(
        ["abs"], ["obliques", "forearms"],
        ["Cuelga de una barra con los brazos estirados.",
         "Sube las piernas (o rodillas) enrollando la pelvis.",
         "Baja controlado sin balancearte."],
        ["Balancearse.", "Subir solo con los flexores de cadera sin enrollar la pelvis."]),
    "Crunch en polea": e(
        ["abs"], ["obliques"],
        ["De rodillas frente a la polea alta, cuerda junto a la cabeza.",
         "Flexiona el tronco llevando los codos a los muslos.",
         "Vuelve lento sin mover la cadera."],
        ["Tirar con los brazos.", "Sentarse sobre los talones."]),
    "Crunch bicicleta": e(
        ["obliques", "abs"], [],
        ["Tumbado boca arriba, manos junto a la cabeza.",
         "Lleva el codo hacia la rodilla contraria mientras estiras la otra pierna.",
         "Alterna lado de forma controlada."],
        ["Tirar del cuello.", "Ir demasiado rápido."]),
    "Pallof press": e(
        ["obliques", "abs"], [],
        ["De lado a la polea, agarre en el pecho.",
         "Estira los brazos al frente resistiendo la rotación.",
         "Aguanta 2 segundos y vuelve."],
        ["Girar el tronco.", "Pies juntos (poca estabilidad)."]),
    "Mountain climbers": e(
        ["abs"], ["quads", "front_delts", "obliques"],
        ["Posición de plancha alta.",
         "Lleva las rodillas al pecho alternando rápido.",
         "Cadera baja y estable."],
        ["Subir la cadera.", "Apoyar el peso atrás."]),

    # ── Cardio / metabólico ──
    "Burpees": e(
        ["quads", "chest"], ["glutes", "abs", "triceps", "calves"],
        ["Desde de pie, baja y apoya las manos.",
         "Salta con los pies atrás a plancha y haz una flexión.",
         "Recoge los pies y salta arriba con los brazos estirados."],
        ["Hundir la cadera en la plancha.", "Aterrizar con las rodillas rígidas."]),
    "Kettlebell swing": e(
        ["glutes", "hamstrings"], ["lower_back", "abs", "front_delts", "forearms"],
        ["Pies algo más abiertos que los hombros, kettlebell entre los pies.",
         "Bisagra de cadera y lanza la pesa entre las piernas.",
         "Extiende la cadera de golpe: la pesa sube a la altura del pecho.",
         "Los brazos solo guían; la fuerza sale de la cadera."],
        ["Hacer una sentadilla.", "Levantar con los brazos o la espalda."]),
    "Jumping jacks": e(
        ["calves", "side_delts"], ["quads", "glutes"],
        ["Salta abriendo piernas y subiendo brazos a la vez.",
         "Vuelve a juntar piernas y bajar brazos.",
         "Aterriza suave sobre la parte delantera del pie."],
        ["Aterrizar con los talones.", "Encoger los hombros."]),
    "Caminata en cinta inclinada": e(
        ["glutes", "calves"], ["hamstrings", "quads"],
        ["Inclinación 8-12 %, velocidad 4,5-6 km/h.",
         "No te agarres a la cinta.",
         "Pasos naturales, tronco erguido."],
        ["Colgarse de las barras.", "Inclinación tan alta que te obliga a agarrarte."]),
    "HIIT bici: 30s fuerte / 60s suave": e(
        ["quads", "glutes"], ["hamstrings", "calves"],
        ["Calienta 5 minutos suave.",
         "30 segundos al máximo esfuerzo, 60 segundos muy suave.",
         "Repite las rondas y termina con 5 minutos suaves."],
        ["No descansar en los intervalos suaves.", "Sillín mal ajustado."]),
}

# Variants of the same movement share the base description
ALIASES = {
    "Curl bíceps barra": "Curl bíceps",
    "Dominadas lastradas": "Dominadas",
    "Press militar mancuernas": "Press militar",
    "Curl femoral sentado": "Curl femoral",
    "Fondos o press cerrado": "Fondos",
    "Sentadilla búlgara en silla": "Sentadilla búlgara",
    "Sentadilla con peso corporal": "Sentadilla",
    "Zancadas alternas": "Zancadas",
    "Zancadas caminando": "Zancadas",
    "Superserie curl + tríceps": None,  # composed below
}

EXERCISES["Superserie curl + tríceps"] = e(
    ["biceps", "triceps"], ["forearms"],
    ["Haz una serie de curl de bíceps y, sin descanso, una de extensión de tríceps.",
     "Descansa al terminar las dos.",
     "Controla la bajada en ambos ejercicios."],
    ["Acelerar y perder la técnica por el cansancio."])


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def get(name: str) -> dict:
    """Exercise info for a routine exercise name (with safe fallback)."""
    base = ALIASES.get(name) or name
    info = EXERCISES.get(base) or EXERCISES.get(name) or e([], [], [], [])
    return {**info, "name": name, "slug": slugify(name), "img": image_for(name, base),
            "video_url": info.get("video") or
            "https://www.youtube.com/results?search_query=" + quote_plus(f"{base} técnica correcta")}


IMG_DIR = Path(__file__).resolve().parent / "static" / "ex"


def image_for(*names) -> str | None:
    """static/ex/ prefix for the first name that has photos, e.g. 'ex/sentadilla'."""
    for n in names:
        if n and (IMG_DIR / f"{slugify(n)}_0.jpg").exists():
            return f"ex/{slugify(n)}"
    return None


BY_SLUG = {slugify(n): n for n in list(EXERCISES) + list(ALIASES)}


def muscle_load(workouts: list) -> dict:
    """Sets per muscle (primary = 1, secondary = 0.5) across the given workouts."""
    load = dict.fromkeys(MUSCLES, 0.0)
    for w in workouts:
        for ex in w.get("exercises", []):
            info = get(ex["name"])
            n = len(ex.get("sets", []))
            for m in info["primary"]:
                load[m] += n
            for m in info["secondary"]:
                load[m] += n * 0.5
    return load


def map_levels(levels: dict) -> dict:
    """Add the combined shoulder shapes the body diagram draws (front / back view)."""
    lv = {k: int(v) for k, v in levels.items()}
    lv["shoulder_f"] = max(lv.get("front_delts", 0), lv.get("side_delts", 0))
    lv["shoulder_b"] = max(lv.get("rear_delts", 0), lv.get("side_delts", 0))
    return lv


def exercise_levels(info: dict) -> dict:
    """Primary muscles at full intensity, secondary ones dimmer."""
    lv = {m: 1 for m in info["secondary"]}
    lv.update({m: 3 for m in info["primary"]})
    return map_levels(lv)


def load_levels(load: dict) -> dict:
    """Weekly sets per muscle -> 0-3 intensity (0, <5, <10, >=10 sets)."""
    return map_levels({m: 0 if v <= 0 else 1 if v < 5 else 2 if v < 10 else 3
                       for m, v in load.items()})


# Photo (start / end position) from the public-domain Free Exercise DB
# (github.com/yuhonas/free-exercise-db). Files live in static/ex/<slug>_0.jpg / _1.jpg.
IMAGE_SOURCES = {
    "Press banca": "Barbell Bench Press - Medium Grip",
    "Press inclinado mancuernas": "Incline Dumbbell Press",
    "Aperturas en polea": "Cable Crossover",
    "Flexiones (rodillas si hace falta)": "Pushups",
    "Fondos": "Dips - Chest Version",
    "Dominadas": "Pullups",
    "Jalón al pecho": "Wide-Grip Lat Pulldown",
    "Remo con barra": "Bent Over Barbell Row",
    "Remo con mancuerna": "One-Arm Dumbbell Row",
    "Remo en polea baja": "Seated Cable Rows",
    "Remo invertido en mesa": "Inverted Row",
    "Face pull": "Face Pull",
    "Peso muerto rumano": "Romanian Deadlift",
    "Superman": "Superman",
    "Press militar": "Standing Military Press",
    "Elevaciones laterales": "Side Lateral Raise",
    "Flexiones pica": "Push-Ups - Close Triceps Position",
    "Curl bíceps": "Dumbbell Bicep Curl",
    "Curl martillo": "Hammer Curls",
    "Extensión tríceps polea": "Triceps Pushdown - Rope Attachment",
    "Press francés": "EZ-Bar Skullcrusher",
    "Fondos en silla": "Bench Dips",
    "Sentadilla": "Barbell Squat",
    "Goblet squat": "Goblet Squat",
    "Prensa de piernas": "Leg Press",
    "Extensión de cuádriceps": "Leg Extensions",
    "Curl femoral": "Lying Leg Curls",
    "Zancadas": "Dumbbell Lunges",
    "Sentadilla búlgara": "Split Squat with Dumbbells",
    "Hip thrust": "Barbell Hip Thrust",
    "Puente de glúteo": "Butt Lift (Bridge)",
    "Peso muerto a una pierna": "Kettlebell One-Legged Deadlift",
    "Elevación de gemelos": "Standing Calf Raises",
    "Plancha": "Plank",
    "Plancha lateral": "Side Bridge",
    "Rueda abdominal": "Ab Roller",
    "Elevación de piernas colgado": "Hanging Leg Raise",
    "Crunch en polea": "Cable Crunch",
    "Crunch bicicleta": "Air Bike",
    "Pallof press": "Pallof Press",
    "Mountain climbers": "Mountain Climbers",
    "Burpees": "Freehand Jump Squat",
    "Kettlebell swing": "One-Arm Kettlebell Swings",
    "Jumping jacks": "Freehand Jump Squat",
    "Caminata en cinta inclinada": "Walking, Treadmill",
    "HIIT bici: 30s fuerte / 60s suave": "Bicycling, Stationary",
    "Superserie curl + tríceps": "Dumbbell Bicep Curl",
    # variants with their own photo
    "Curl bíceps barra": "Barbell Curl",
    "Dominadas lastradas": "Pullups",
    "Press militar mancuernas": "Dumbbell Shoulder Press",
    "Curl femoral sentado": "Seated Leg Curl",
    "Sentadilla con peso corporal": "Bodyweight Squat",
    "Zancadas caminando": "Bodyweight Walking Lunge",
    "Zancadas alternas": "Dumbbell Lunges",
    "Sentadilla búlgara en silla": "Split Squats",
    "Fondos o press cerrado": "Dips - Triceps Version",
}
# Burpees / jumping jacks / pike push-ups have no matching photo; don't show a misleading one
IMAGE_SOURCES.pop("Burpees")
IMAGE_SOURCES.pop("Jumping jacks")
IMAGE_SOURCES.pop("Flexiones pica")

"""Estimación de macros a partir de una foto del plato (o una descripción) con Claude."""

import base64
import json
import os

import anthropic

MODEL = os.environ.get("AI_MODEL", "claude-opus-5-5")

SYSTEM = """Eres un nutricionista experto en cocina española y mediterránea.
Recibes la foto de un plato o una descripción de lo que ha comido alguien.
Tu tarea: identificar cada alimento, estimar su peso en gramos TAL COMO SE VE
(cocinado, escurrido) y calcular calorías y macros de esa cantidad usando
tablas de composición de referencia (BEDCA / USDA).

Reglas:
- Un item por alimento reconocible (p. ej. "Arroz blanco cocido", "Pechuga de pollo a la plancha").
- Si el plato lleva aceite o salsa visible o típica de la receta, añádelo como item aparte.
- Usa el tamaño del plato, cubiertos o manos como referencia de escala.
- Los valores de calories/protein/carbs/fat son del TOTAL de ese item (no por 100 g).
- Nombres en español, cortos y claros.
- Si la imagen no contiene comida, devuelve items vacío y explícalo en notes."""

SCHEMA = {
    "type": "object",
    "properties": {
        "dish": {"type": "string", "description": "Nombre corto del plato"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "grams": {"type": "number"},
                    "calories": {"type": "number"},
                    "protein": {"type": "number"},
                    "carbs": {"type": "number"},
                    "fat": {"type": "number"},
                },
                "required": ["name", "grams", "calories", "protein", "carbs", "fat"],
                "additionalProperties": False,
            },
        },
        "confidence": {"type": "string", "enum": ["alta", "media", "baja"]},
        "notes": {"type": "string", "description": "Aclaraciones breves para el usuario"},
    },
    "required": ["dish", "items", "confidence", "notes"],
    "additionalProperties": False,
}


class AIError(Exception):
    pass


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def analyze_meal(image: bytes | None = None, media_type: str = "image/jpeg",
                 description: str = "") -> dict:
    if not is_configured():
        raise AIError("Falta configurar ANTHROPIC_API_KEY en el servidor.")

    content = []
    if image:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": media_type,
            "data": base64.standard_b64encode(image).decode()}})
    text = "Analiza esta comida y estima sus macros."
    if description:
        text += f"\nDetalles del usuario: {description}"
    content.append({"type": "text", "text": text})

    client = anthropic.Anthropic(timeout=90.0)
    params = dict(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": content}],
    )
    try:
        try:
            # Server-side fallback: if the model declines, another model retries in the same call
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
        except anthropic.BadRequestError:
            # e.g. AI_MODEL set to a model/platform without fallback support
            response = client.messages.create(**params)
    except anthropic.AuthenticationError:
        raise AIError("La clave de la API de Claude no es válida.")
    except anthropic.RateLimitError:
        raise AIError("Demasiadas peticiones. Prueba en un minuto.")
    except anthropic.APIConnectionError:
        raise AIError("No se pudo conectar con el servicio de IA.")
    except anthropic.APIStatusError as e:
        raise AIError(f"Error del servicio de IA ({e.status_code}).")

    if response.stop_reason == "refusal":
        raise AIError("La IA no ha podido analizar esta imagen.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise AIError("Respuesta de la IA incompleta. Vuelve a intentarlo.")

    for it in data["items"]:
        it["grams"] = max(round(it["grams"]), 1)
        for k in ("calories", "protein", "carbs", "fat"):
            it[k] = round(max(it[k], 0), 1)
    return data

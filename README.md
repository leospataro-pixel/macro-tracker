# Macros Familia

App web (PWA) para controlar macros, comidas y entrenamientos de toda la familia desde el móvil.

## Qué hace

- **Perfiles familiares**: cada miembro con sus datos, objetivo (perder grasa, mantener, recomposición, ganar músculo) y macros calculados automáticamente (Mifflin-St Jeor + actividad + objetivo). Se recalculan al registrar el peso.
- **Registro rápido de comidas**:
  - 📷 **Foto del plato** → la IA (Claude) identifica los alimentos, estima gramos y macros. Ajustas los gramos si hace falta y lo guardas.
  - También puedes **describirlo con texto** ("2 huevos fritos con pan").
  - ⭐ **Frecuentes**: un toque y queda registrado con la cantidad de la última vez.
  - 🔁 **Repetir** el desayuno/comida/cena de ayer.
  - 🔍 Buscador con porciones rápidas (1 huevo, 2 rebanadas, 100 g…).
- **Qué comer hoy**: plan con gramos exactos para las comidas que te quedan, ajustado a lo que ya has comido. Botón "Me lo he comido" para registrarlo de golpe.
- **Entrenamiento**: rutinas recomendadas según objetivo y nivel (gimnasio y casa), registro de series/peso/reps con lo de la última vez como referencia, cardio y historial.
- **Recordatorios push** para desayuno, media mañana, comida, merienda, cena y entreno. Si ya has registrado esa comida, no avisa.
- **Resumen familiar**: calorías, proteína, comidas registradas y entrenos de la semana de cada miembro.

## Configuración (variables de entorno)

| Variable | Obligatoria | Para qué |
|---|---|---|
| `ANTHROPIC_API_KEY` | Para fotos | Clave de la API de Claude (console.anthropic.com) |
| `SECRET_KEY` | Sí en producción | Firma de la sesión. Pon un texto largo y aleatorio |
| `DATA_DIR` | Recomendada | Carpeta de datos. En Railway, apúntala a un volumen persistente (p. ej. `/data`) |
| `APP_PIN` | No | PIN familiar para que nadie más entre en la app |
| `APP_TZ` | No | Zona horaria de los recordatorios (por defecto `Europe/Madrid`) |
| `VAPID_PRIVATE_KEY` | No | Clave PEM para push. Si no se pone, se genera y guarda en `DATA_DIR` |
| `VAPID_SUBJECT` | No | Contacto para el servicio push (`mailto:tu@email`) |
| `AI_MODEL` | No | Modelo de Claude (por defecto `claude-opus-5-5`) |

## Ejecutar en local

```bash
pip install -r requirements.txt
python app.py        # http://localhost:5000
```

## Notificaciones en el móvil

- **Android (Chrome)**: Perfil → Comidas y recordatorios → *Activar notificaciones*.
- **iPhone (iOS 16.4+)**: en Safari, *Compartir → Añadir a pantalla de inicio*, abre la app desde el icono y actívalas desde la misma pantalla.
- Las notificaciones push necesitan HTTPS (Railway lo da por defecto).

Los datos se guardan en ficheros JSON dentro de `DATA_DIR`. Sin volumen persistente se pierden en cada despliegue.

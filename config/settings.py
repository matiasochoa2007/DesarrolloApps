"""Configuración general de Orthoimagen Dental.

Aquí viven los valores que no son lógica de negocio: la ruta de la base de
datos y los parámetros de seguridad. No se guardan claves ni secretos.
"""

import os
from pathlib import Path

# Carpeta raíz del repositorio (DesarrolloApps/).
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Ruta de la base SQLite (RF-09). Se puede cambiar con la variable de
# entorno ORTHOIMAGEN_BD, por ejemplo para usar una base de pruebas.
RUTA_BD = Path(
    os.environ.get("ORTHOIMAGEN_BD", RAIZ_PROYECTO / "data" / "orthoimagen.db")
)

# Horario de atención (RF-07). Supuesto del equipo: el documento no fija el
# horario; se ofrecen bloques de 60 minutos de 09:00 a 18:00 (último inicio
# 17:00). RF-02 compara la hora de inicio (ambigüedad resuelta en el plan).
HORA_APERTURA = "09:00"
HORA_CIERRE = "18:00"
DURACION_BLOQUE_MIN = 60

# Iteraciones de PBKDF2-SHA256 para el hash de contraseñas (RF-11).
ITERACIONES_HASH = 120_000

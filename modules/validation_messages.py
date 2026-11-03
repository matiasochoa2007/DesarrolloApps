"""M6 Validación y mensajes - Orthoimagen Dental.

Revisa que los datos de una cita estén completos y devuelve mensajes claros
que nombran el campo faltante o el conflicto de horario.

Requerimiento: RF-10 (apoyo a RF-01).
Historia: HU-15 (apoyo a HU-01).
Criterios: CA-45 (normal), CA-46 (límite), CA-47 (error), CA-03 (apoyo).

Alcance de este módulo:
- Son funciones puras: no leen ni escriben datos, no hacen login.
- No calcula disponibilidad: el indicador de horario ocupado lo entrega M3.
- No valida formatos de fecha u hora ni modifica los datos recibidos.
"""

from collections.abc import Mapping

# Campos obligatorios, en el orden en que se reportan en los mensajes.
CAMPOS_OBLIGATORIOS = ("fecha", "hora", "dentista", "servicio")
CAMPO_PACIENTE = "paciente"

# Mensajes exactos aprobados por el equipo.
MENSAJE_CAMPO_FALTANTE = (
    "Error: El campo '{campo}' es obligatorio. Por favor, complételo."
)
MENSAJE_CAMPOS_FALTANTES = (
    "Error: Los siguientes campos son obligatorios y están vacíos: {campos}."
)
MENSAJE_HORARIO_OCUPADO = (
    "Error: El horario seleccionado no está disponible. "
    "Por favor, elija un horario diferente."
)


def esta_vacio(valor):
    """Indica si un valor cuenta como vacío.

    Es vacío: None, una cadena vacía o una cadena con solo espacios.
    Cualquier otro valor se considera capturado.
    """
    if valor is None:
        return True
    if isinstance(valor, str):
        return valor.strip() == ""
    return False


def obtener_campos_faltantes(datos, requiere_paciente=False):
    """Devuelve la lista de campos obligatorios vacíos o ausentes.

    El orden es siempre: fecha, hora, dentista, servicio y, si
    requiere_paciente es True, paciente. No modifica `datos`.

    `datos` puede ser None (se trata como un formulario sin captura).
    Si no es un diccionario (ni None) se lanza TypeError.
    """
    if datos is None:
        datos = {}
    if not isinstance(datos, Mapping):
        raise TypeError("'datos' debe ser un diccionario o None.")

    campos = list(CAMPOS_OBLIGATORIOS)
    if requiere_paciente:
        campos.append(CAMPO_PACIENTE)

    return [campo for campo in campos if esta_vacio(datos.get(campo))]


def construir_mensaje_faltantes(campos_faltantes):
    """Arma el mensaje de error para uno o varios campos faltantes.

    Un campo: nombra ese campo (CA-45 / CA-03).
    Varios campos: los lista todos separados por coma (CA-46).
    Sin campos faltantes devuelve una cadena vacía.
    """
    if not campos_faltantes:
        return ""
    if len(campos_faltantes) == 1:
        return MENSAJE_CAMPO_FALTANTE.format(campo=campos_faltantes[0])
    return MENSAJE_CAMPOS_FALTANTES.format(campos=", ".join(campos_faltantes))


def validar_cita(datos, horario_ocupado=False, requiere_paciente=False):
    """Valida los datos de una cita y devuelve el resultado.

    Parámetros:
        datos: diccionario con fecha, hora, dentista, servicio y, si lo
            registra la recepcionista, paciente.
        horario_ocupado: indicador que entrega M3 Disponibilidad
            (True si el horario ya está ocupado).
        requiere_paciente: True cuando registra la recepcionista, porque
            ella sí captura el nombre del paciente (HU-02).

    Devuelve un diccionario:
        {"valido": bool, "campos_faltantes": list, "mensaje": str}
    El mensaje es una cadena vacía cuando los datos son válidos.

    Prioridad: primero se reportan los campos faltantes; el conflicto de
    horario solo se reporta si los datos están completos (CA-47).
    """
    faltantes = obtener_campos_faltantes(datos, requiere_paciente)
    if faltantes:
        return {
            "valido": False,
            "campos_faltantes": faltantes,
            "mensaje": construir_mensaje_faltantes(faltantes),
        }

    if horario_ocupado:
        return {
            "valido": False,
            "campos_faltantes": [],
            "mensaje": MENSAJE_HORARIO_OCUPADO,
        }

    return {"valido": True, "campos_faltantes": [], "mensaje": ""}

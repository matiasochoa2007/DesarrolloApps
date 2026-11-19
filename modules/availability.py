"""M3 Disponibilidad - Orthoimagen Dental.

Calcula los horarios libres de un dentista y le entrega a M6 el indicador de
horario ocupado.

Requerimientos: RF-07 (HU-12, HU-13) y RF-02 (HU-03).
Criterios: CA-36 a CA-41 y CA-07 a CA-09.

Regla RF-02 (ambigüedad resuelta en el plan): "mismo horario" significa la
misma hora de inicio. Las citas canceladas liberan el horario.
"""

from datetime import date, datetime, timedelta

from config import settings
from modules.auth_roles import ROL_RECEPCIONISTA, verificar_permiso
from modules.data_access import ErrorBaseDatos
from modules.validation_messages import esta_vacio

MENSAJE_FECHA_INVALIDA = (
    "Error: La fecha '{fecha}' no es válida. Use el formato AAAA-MM-DD."
)
MENSAJE_FECHA_PASADA = (
    "Error: La fecha '{fecha}' ya pasó. Elija una fecha de hoy en adelante."
)
MENSAJE_HORA_INVALIDA = (
    "Error: La hora '{hora}' no es un horario de atención. "
    "Elija uno de: {horarios}."
)
MENSAJE_DENTISTA_INEXISTENTE = (
    "Error: El dentista seleccionado no existe o no está activo."
)
MENSAJE_SIN_HORARIOS = (
    "Aviso: El dentista no tiene horarios libres el {fecha}. "
    "Pruebe con otra fecha u otro dentista."
)


def _a_minutos(hora):
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def horarios_del_dia():
    """Horas de inicio de los bloques de atención, en formato HH:MM."""
    inicio = _a_minutos(settings.HORA_APERTURA)
    fin = _a_minutos(settings.HORA_CIERRE)
    paso = settings.DURACION_BLOQUE_MIN
    return [
        f"{minuto // 60:02d}:{minuto % 60:02d}"
        for minuto in range(inicio, fin - paso + 1, paso)
    ]


def validar_fecha(fecha, hoy=None, permitir_pasadas=False):
    """Devuelve "" si la fecha es válida y no está en el pasado; si no, el
    mensaje de error. Para consultas (RF-06) se permiten fechas pasadas."""
    if esta_vacio(fecha):
        return MENSAJE_FECHA_INVALIDA.format(fecha="")
    texto = str(fecha).strip()
    try:
        dia = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return MENSAJE_FECHA_INVALIDA.format(fecha=texto)
    if not permitir_pasadas and dia < (hoy or date.today()):
        return MENSAJE_FECHA_PASADA.format(fecha=texto)
    return ""


def validar_hora(hora):
    """Devuelve "" si la hora es un inicio de bloque válido; si no, el error."""
    horarios = horarios_del_dia()
    if str(hora).strip() in horarios:
        return ""
    return MENSAJE_HORA_INVALIDA.format(hora=hora, horarios=", ".join(horarios))


def obtener_dentista_activo(bd, id_odontologo):
    """Devuelve el odontólogo si existe y está activo; si no, None."""
    try:
        id_odontologo = int(id_odontologo)
    except (TypeError, ValueError):
        return None
    odontologo = bd.obtener_odontologo(id_odontologo)
    if odontologo is None or not odontologo["activo"]:
        return None
    return odontologo


def horario_ocupado(bd, id_odontologo, fecha, hora, excluir_id_cita=None):
    """Indicador para M6 (CA-47): True si el dentista ya tiene una cita activa
    con esa hora de inicio ese día (RF-02). Puede lanzar ErrorBaseDatos."""
    return str(hora).strip() in bd.horas_ocupadas(
        int(id_odontologo), str(fecha).strip(), excluir_id_cita
    )


def consultar_disponibilidad(bd, sesion, id_odontologo, fecha, hoy=None):
    """Horarios libres de un dentista en una fecha (HU-12, HU-13).

    Devuelve {"exito", "mensaje", "libres", "ocupados", "dentista"}.
    La recepcionista también recibe la lista de horarios ocupados; el
    paciente solo ve los libres.
    """
    resultado = {"exito": False, "mensaje": "", "libres": [], "ocupados": [],
                 "dentista": None}

    permiso = verificar_permiso(sesion, "consultar_disponibilidad")
    if not permiso["exito"]:
        resultado["mensaje"] = permiso["mensaje"]
        return resultado

    error_fecha = validar_fecha(fecha, hoy)
    if error_fecha:
        resultado["mensaje"] = error_fecha
        return resultado

    try:
        dentista = obtener_dentista_activo(bd, id_odontologo)
        if dentista is None:
            resultado["mensaje"] = MENSAJE_DENTISTA_INEXISTENTE
            return resultado
        ocupadas = set(bd.horas_ocupadas(dentista["id_odontologo"],
                                         str(fecha).strip()))
    except ErrorBaseDatos as error:
        resultado["mensaje"] = error.mensaje
        return resultado

    todas = horarios_del_dia()
    if str(fecha).strip() == (hoy or date.today()).isoformat():
        ahora = datetime.now().strftime("%H:%M")
        todas = [h for h in todas if h > ahora]

    resultado["exito"] = True
    resultado["dentista"] = dentista
    resultado["libres"] = [h for h in todas if h not in ocupadas]
    if sesion.get("rol") == ROL_RECEPCIONISTA:
        resultado["ocupados"] = sorted(ocupadas)
    if not resultado["libres"]:
        resultado["mensaje"] = MENSAJE_SIN_HORARIOS.format(fecha=str(fecha).strip())
    return resultado


def fecha_de_manana():
    """Ayuda para la consola: fecha de mañana en formato AAAA-MM-DD."""
    return (date.today() + timedelta(days=1)).isoformat()

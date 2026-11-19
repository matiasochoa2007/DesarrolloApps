"""M4 Consulta de agenda - Orthoimagen Dental.

Muestra citas filtradas según quién consulta.

Requerimiento: RF-06.
Historias: HU-09 (paciente ve sus citas), HU-10 (recepcionista filtra por
día, dentista o paciente), HU-11 (dentista ve su agenda del día).
Criterios: CA-27 a CA-35. Cierra el diferido CA-01 del Incremento 3.
"""

from modules.auth_roles import verificar_permiso
from modules.availability import MENSAJE_DENTISTA_INEXISTENTE, validar_fecha
from modules.data_access import ErrorBaseDatos
from modules.validation_messages import esta_vacio

MENSAJE_SIN_CITAS_PACIENTE = "Aviso: No tiene citas registradas."
MENSAJE_SIN_RESULTADOS = "Aviso: No hay citas que coincidan con el filtro."
MENSAJE_SIN_CITAS_DIA = "Aviso: No tiene citas programadas el {fecha}."
MENSAJE_SOLO_PROPIAS = "Error: Solo puede consultar sus propias citas."
MENSAJE_SOLO_AGENDA_PROPIA = "Error: Solo puede consultar su propia agenda."
MENSAJE_PACIENTE_INEXISTENTE = "Error: El paciente seleccionado no existe."
MENSAJE_FILTRO_INVALIDO = "Error: El valor del filtro '{campo}' no es válido."


def _resultado(exito, mensaje="", citas=None):
    return {"exito": exito, "mensaje": mensaje, "citas": citas or []}


def _a_entero(valor):
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def mis_citas(bd, sesion, id_paciente=None):
    """El paciente ve todas sus citas con su estatus (HU-09).

    Si pide las de otro paciente se rechaza (CA-29).
    """
    permiso = verificar_permiso(sesion, "ver_mis_citas")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"])
    propio = sesion["id_paciente"]
    if id_paciente is not None and _a_entero(id_paciente) != propio:
        return _resultado(False, MENSAJE_SOLO_PROPIAS)
    try:
        citas = bd.consultar_citas(id_paciente=propio)
    except ErrorBaseDatos as error:
        return _resultado(False, error.mensaje)
    return _resultado(True, "" if citas else MENSAJE_SIN_CITAS_PACIENTE, citas)


def filtrar_citas(bd, sesion, fecha=None, id_odontologo=None, id_paciente=None):
    """La recepcionista filtra por día, dentista o paciente (HU-10).

    Los filtros vacíos no se aplican. Fechas pasadas sí se permiten porque
    también sirve para revisar el historial.
    """
    permiso = verificar_permiso(sesion, "filtrar_citas")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"])

    filtros = {}
    try:
        if not esta_vacio(fecha):
            error = validar_fecha(fecha, permitir_pasadas=True)
            if error:
                return _resultado(False, error)
            filtros["fecha"] = str(fecha).strip()
        if not esta_vacio(id_odontologo):
            filtros["id_odontologo"] = _a_entero(id_odontologo)
            if (filtros["id_odontologo"] is None
                    or bd.obtener_odontologo(filtros["id_odontologo"]) is None):
                return _resultado(False, MENSAJE_DENTISTA_INEXISTENTE)
        if not esta_vacio(id_paciente):
            filtros["id_paciente"] = _a_entero(id_paciente)
            if (filtros["id_paciente"] is None
                    or bd.obtener_paciente(filtros["id_paciente"]) is None):
                return _resultado(False, MENSAJE_PACIENTE_INEXISTENTE)
        citas = bd.consultar_citas(**filtros)
    except ErrorBaseDatos as error:
        return _resultado(False, error.mensaje)
    return _resultado(True, "" if citas else MENSAJE_SIN_RESULTADOS, citas)


def agenda_dentista(bd, sesion, fecha, id_odontologo=None):
    """El dentista ve sus citas activas de un día (HU-11).

    Si pide la agenda de otro dentista se rechaza (CA-35).
    """
    permiso = verificar_permiso(sesion, "ver_agenda_dentista")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"])
    propio = sesion["id_odontologo"]
    if id_odontologo is not None and _a_entero(id_odontologo) != propio:
        return _resultado(False, MENSAJE_SOLO_AGENDA_PROPIA)
    error = validar_fecha(fecha, permitir_pasadas=True)
    if error:
        return _resultado(False, error)
    fecha = str(fecha).strip()
    try:
        citas = bd.consultar_citas(id_odontologo=propio, fecha=fecha,
                                   incluir_canceladas=False)
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje)
    mensaje = "" if citas else MENSAJE_SIN_CITAS_DIA.format(fecha=fecha)
    return _resultado(True, mensaje, citas)


def formatear_cita(cita):
    """Texto de una línea para mostrar una cita en pantalla."""
    motivo = f" · {cita['motivo']}" if cita.get("motivo") else ""
    return (
        f"[{cita['id_cita']}] {cita['fecha']} {cita['hora']} · "
        f"{cita['paciente']} con {cita['dentista']} · {cita['servicio']} · "
        f"{cita['estatus']}{motivo}"
    )

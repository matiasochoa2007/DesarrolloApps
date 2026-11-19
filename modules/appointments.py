"""M2 Gestión de citas - Orthoimagen Dental.

Registra citas usando M6 (mensajes), M3 (disponibilidad) y M7 (datos).

Requerimiento: RF-01 (HU-01 paciente, HU-02 recepcionista).
Criterios: CA-01 a CA-06; reutiliza CA-45 a CA-47 (M6) y RF-02 (M3).

Datos de una cita (diccionario):
    fecha (AAAA-MM-DD), hora (HH:MM), dentista (id_odontologo),
    servicio (id_servicio), paciente (id_paciente, solo recepcionista),
    motivo (opcional).
"""

from modules.auth_roles import ROL_PACIENTE, ROL_RECEPCIONISTA, verificar_permiso
from modules.availability import (
    MENSAJE_DENTISTA_INEXISTENTE,
    horario_ocupado,
    obtener_dentista_activo,
    validar_fecha,
    validar_hora,
)
from modules.data_access import (
    ESTATUS_ATENDIDA,
    ESTATUS_CANCELADA,
    ESTATUS_REPROGRAMADA,
    ErrorBaseDatos,
    ErrorIntegridad,
)
from modules.validation_messages import (
    MENSAJE_HORARIO_OCUPADO,
    esta_vacio,
    validar_cita,
)

MENSAJE_SERVICIO_INEXISTENTE = "Error: El servicio seleccionado no existe."
MENSAJE_PACIENTE_INEXISTENTE = "Error: El paciente seleccionado no existe."
MENSAJE_CITA_REGISTRADA = (
    "Cita registrada: {fecha} a las {hora} con {dentista} ({servicio}). "
    "Folio {id_cita}."
)
MENSAJE_CITA_MODIFICADA = (
    "Cita {id_cita} modificada: {fecha} a las {hora} con {dentista} "
    "({servicio}). Estatus: {estatus}."
)
MENSAJE_CITA_INEXISTENTE = "Error: La cita '{id_cita}' no existe."
MENSAJE_CITA_AJENA = (
    "Error: Solo puede modificar o cancelar sus propias citas."
)
MENSAJE_CITA_NO_MODIFICABLE = (
    "Error: La cita {id_cita} está {estatus} y ya no se puede modificar."
)
MENSAJE_CAMBIO_DENTISTA_RECEPCION = (
    "Error: Para cambiar de dentista solicítelo en recepción."
)

# Campos que se pueden cambiar al modificar una cita.
CAMPOS_MODIFICABLES = ("fecha", "hora", "dentista", "servicio", "motivo")


def _resultado(exito, mensaje, **datos):
    return {"exito": exito, "mensaje": mensaje, **datos}


def _a_entero(valor):
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def _limpiar(datos):
    """Copia de los datos con espacios recortados (no modifica el original)."""
    return {
        clave: valor.strip() if isinstance(valor, str) else valor
        for clave, valor in (datos or {}).items()
    }


def validar_datos_de_cita(bd, datos, requiere_paciente, hoy=None,
                          excluir_id_cita=None):
    """Aplica en orden todas las validaciones de una cita.

    1. Campos obligatorios (M6: CA-45, CA-46).
    2. Formato y vigencia de fecha y hora (M3).
    3. Que existan el dentista, el servicio y, si aplica, el paciente.
    4. Horario ocupado del dentista (M3 → M6: CA-47, RF-02).

    Devuelve "" si todo es válido o el primer mensaje de error.
    Puede lanzar ErrorBaseDatos.
    """
    revision = validar_cita(datos, requiere_paciente=requiere_paciente)
    if not revision["valido"]:
        return revision["mensaje"]

    error = validar_fecha(datos["fecha"], hoy) or validar_hora(datos["hora"])
    if error:
        return error

    if obtener_dentista_activo(bd, datos["dentista"]) is None:
        return MENSAJE_DENTISTA_INEXISTENTE
    id_servicio = _a_entero(datos["servicio"])
    if id_servicio is None or bd.obtener_servicio(id_servicio) is None:
        return MENSAJE_SERVICIO_INEXISTENTE
    if requiere_paciente:
        id_paciente = _a_entero(datos["paciente"])
        if id_paciente is None or bd.obtener_paciente(id_paciente) is None:
            return MENSAJE_PACIENTE_INEXISTENTE

    ocupado = horario_ocupado(bd, datos["dentista"], datos["fecha"],
                              datos["hora"], excluir_id_cita)
    return validar_cita(datos, ocupado, requiere_paciente)["mensaje"]


def registrar_cita(bd, sesion, datos, hoy=None):
    """Registra una cita nueva con estatus "Programada".

    - Paciente (HU-01): la cita queda a su nombre; no captura paciente.
    - Recepcionista (HU-02): debe indicar el paciente.
    - Dentista: no puede registrar citas.

    Devuelve {"exito", "mensaje", "id_cita"}.
    """
    rol = (sesion or {}).get("rol")
    accion = ("registrar_cita_para_paciente" if rol == ROL_RECEPCIONISTA
              else "registrar_cita_propia")
    permiso = verificar_permiso(sesion, accion)
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"], id_cita=None)

    datos = _limpiar(datos)
    requiere_paciente = rol == ROL_RECEPCIONISTA
    if rol == ROL_PACIENTE:
        datos["paciente"] = sesion["id_paciente"]

    try:
        error = validar_datos_de_cita(bd, datos, requiere_paciente, hoy)
        if error:
            return _resultado(False, error, id_cita=None)
        id_cita = bd.insertar_cita(
            datos["fecha"], datos["hora"], _a_entero(datos["paciente"]),
            _a_entero(datos["dentista"]), _a_entero(datos["servicio"]),
            None if esta_vacio(datos.get("motivo")) else datos["motivo"],
        )
        cita = bd.obtener_cita(id_cita)
    except ErrorIntegridad:
        # Otro usuario tomó el horario entre la validación y el guardado.
        return _resultado(False, MENSAJE_HORARIO_OCUPADO, id_cita=None)
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje, id_cita=None)

    return _resultado(True, MENSAJE_CITA_REGISTRADA.format(**cita), id_cita=id_cita)


# -- Citas existentes (Incremento 4) --------------------------------------------

def obtener_cita_autorizada(bd, sesion, id_cita, accion):
    """Busca la cita y revisa que la sesión pueda actuar sobre ella.

    Devuelve (cita, "") o (None, mensaje de error). El paciente solo puede
    actuar sobre sus propias citas. Puede lanzar ErrorBaseDatos.
    """
    permiso = verificar_permiso(sesion, accion)
    if not permiso["exito"]:
        return None, permiso["mensaje"]
    numero = _a_entero(id_cita)
    cita = bd.obtener_cita(numero) if numero is not None else None
    if cita is None:
        return None, MENSAJE_CITA_INEXISTENTE.format(id_cita=str(id_cita).strip())
    if sesion["rol"] == ROL_PACIENTE and cita["id_paciente"] != sesion["id_paciente"]:
        return None, MENSAJE_CITA_AJENA
    return cita, ""


def modificar_cita(bd, sesion, id_cita, cambios, hoy=None):
    """Modifica fecha, hora, servicio o motivo de una cita (HU-04, HU-05).

    - Solo los campos presentes en `cambios` se modifican; un campo presente
      pero vacío se rechaza con el mensaje de M6 (CA-16).
    - La recepcionista también puede cambiar el dentista (CA-14).
    - La cita no choca consigo misma (CA-11) y el horario anterior queda
      libre al moverla (CA-10).
    - Si cambia fecha, hora o dentista, el estatus pasa a "Reprogramada".

    Devuelve {"exito", "mensaje", "id_cita"}.
    """
    cambios = _limpiar(cambios)
    try:
        cita, error = obtener_cita_autorizada(bd, sesion, id_cita, "modificar_cita")
        if error:
            return _resultado(False, error, id_cita=None)
        if cita["estatus"] in (ESTATUS_CANCELADA, ESTATUS_ATENDIDA):
            return _resultado(False, MENSAJE_CITA_NO_MODIFICABLE.format(**cita),
                              id_cita=cita["id_cita"])
        if sesion["rol"] == ROL_PACIENTE and "dentista" in cambios and \
                _a_entero(cambios["dentista"]) != cita["id_odontologo"]:
            return _resultado(False, MENSAJE_CAMBIO_DENTISTA_RECEPCION,
                              id_cita=cita["id_cita"])

        datos = {"fecha": cita["fecha"], "hora": cita["hora"],
                 "dentista": cita["id_odontologo"], "servicio": cita["id_servicio"],
                 "motivo": cita["motivo"]}
        datos.update({campo: valor for campo, valor in cambios.items()
                      if campo in CAMPOS_MODIFICABLES})

        error = validar_datos_de_cita(bd, datos, requiere_paciente=False, hoy=hoy,
                                      excluir_id_cita=cita["id_cita"])
        if error:
            return _resultado(False, error, id_cita=cita["id_cita"])

        nueva = (datos["fecha"], datos["hora"], _a_entero(datos["dentista"]))
        anterior = (cita["fecha"], cita["hora"], cita["id_odontologo"])
        estatus = ESTATUS_REPROGRAMADA if nueva != anterior else cita["estatus"]
        bd.actualizar_cita(
            cita["id_cita"], datos["fecha"], datos["hora"],
            _a_entero(datos["dentista"]), _a_entero(datos["servicio"]),
            None if esta_vacio(datos.get("motivo")) else datos["motivo"], estatus,
        )
        actualizada = bd.obtener_cita(cita["id_cita"])
    except ErrorIntegridad:
        return _resultado(False, MENSAJE_HORARIO_OCUPADO, id_cita=None)
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje, id_cita=None)

    return _resultado(True, MENSAJE_CITA_MODIFICADA.format(**actualizada),
                      id_cita=actualizada["id_cita"])

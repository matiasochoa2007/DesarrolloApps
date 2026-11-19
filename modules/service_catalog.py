"""M5 Catálogo de servicios - Orthoimagen Dental.

Muestra los servicios de la clínica con su duración y precio.

Requerimiento: RF-08. Historia: HU-14. Criterios: CA-42, CA-43, CA-44.
"""

from modules.auth_roles import verificar_permiso
from modules.data_access import ErrorBaseDatos

MENSAJE_CATALOGO_VACIO = (
    "Aviso: Por el momento no hay servicios registrados en el catálogo."
)


def consultar_catalogo(bd, sesion):
    """Devuelve los servicios ordenados por nombre.

    Devuelve {"exito", "mensaje", "servicios"}:
    - con servicios: exito True y la lista (CA-42);
    - catálogo vacío: exito True, lista vacía y aviso claro (CA-43);
    - base no disponible: exito False y mensaje de error (CA-44).
    """
    permiso = verificar_permiso(sesion, "consultar_catalogo")
    if not permiso["exito"]:
        return {"exito": False, "mensaje": permiso["mensaje"], "servicios": []}
    try:
        servicios = bd.listar_servicios()
    except ErrorBaseDatos as error:
        return {"exito": False, "mensaje": error.mensaje, "servicios": []}
    mensaje = "" if servicios else MENSAJE_CATALOGO_VACIO
    return {"exito": True, "mensaje": mensaje, "servicios": servicios}


def formatear_servicio(servicio):
    """Texto de una línea para mostrar un servicio en pantalla."""
    precio = servicio.get("precio")
    texto_precio = f"${precio:,.2f} MXN" if precio is not None else "precio a consultar"
    return (
        f"[{servicio['id_servicio']}] {servicio['nombre']} · "
        f"{servicio['duracion_min']} min · {texto_precio}"
    )

"""Puente entre la interfaz web (HTML/JS) y los módulos M1 a M8.

La ventana de escritorio (pywebview) y el servidor de desarrollo llaman a
los métodos públicos de `ApiOrthoimagen`. Aquí no hay reglas de negocio:
cada método toma la sesión activa, llama al módulo correspondiente y
devuelve un diccionario serializable con "exito" y "mensaje".
"""

import functools
import traceback
from datetime import date, timedelta

from modules import agenda, appointments, availability, patients
from modules.auth_roles import (
    ROL_DENTISTA,
    ROL_PACIENTE,
    ROL_RECEPCIONISTA,
    iniciar_sesion,
)
from modules.data_access import ESTATUS_CANCELADA, ErrorBaseDatos
from modules.demo_data import USUARIOS_DEMO
from modules.service_catalog import consultar_catalogo

MENSAJE_INESPERADO = (
    "Error: Ocurrió un problema inesperado. Intente de nuevo; si continúa, "
    "avise a la recepción."
)
ACTIVAS = ("Programada", "Reprogramada")


def _seguro(metodo):
    """Ningún error de Python debe congelar la interfaz: se responde con un
    mensaje claro (RF-10) y el detalle se imprime para depurar."""

    @functools.wraps(metodo)
    def envoltura(self, *args, **kwargs):
        try:
            return metodo(self, *args, **kwargs)
        except ErrorBaseDatos as error:
            return {"exito": False, "mensaje": error.mensaje}
        except Exception:  # pragma: no cover - red de seguridad
            traceback.print_exc()
            return {"exito": False, "mensaje": MENSAJE_INESPERADO}

    return envoltura


def _iniciales(texto):
    partes = [p for p in str(texto).replace(".", " ").split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "?"


class ApiOrthoimagen:
    def __init__(self, bd, modo_demo=True, hoy=None):
        self._bd = bd
        self._sesion = None
        self._modo_demo = modo_demo
        self._hoy = hoy

    # -- Utilidades internas -------------------------------------------------

    def _fecha_hoy(self):
        return self._hoy or date.today()

    def _perfil(self):
        """Sesión con nombre visible para la interfaz."""
        if self._sesion is None:
            return None
        sesion = dict(self._sesion)
        rol = sesion["rol"]
        if rol == ROL_PACIENTE:
            p = self._bd.obtener_paciente(sesion["id_paciente"])
            sesion["nombre"] = f"{p['nombre']} {p['apellidos']}" if p else sesion["nombre_usuario"]
            sesion["detalle"] = "Paciente"
        elif rol == ROL_DENTISTA:
            o = self._bd.obtener_odontologo(sesion["id_odontologo"])
            sesion["nombre"] = f"Dr(a). {o['nombre']} {o['apellidos']}" if o else sesion["nombre_usuario"]
            sesion["detalle"] = (o or {}).get("especialidad") or "Dentista"
        else:
            sesion["nombre"] = "Recepción"
            sesion["detalle"] = sesion["nombre_usuario"]
        sesion["iniciales"] = _iniciales(sesion["nombre"].replace("Dr(a).", ""))
        return sesion

    @staticmethod
    def _futuras(citas, hoy):
        return [c for c in citas if c["estatus"] in ACTIVAS and c["fecha"] >= hoy]

    # -- Sesión ----------------------------------------------------------------

    @_seguro
    def estado(self):
        """Datos para arrancar la interfaz."""
        demo = []
        if self._modo_demo:
            demo = [{"usuario": u, "contrasena": c, "rol": r} for u, c, r, _ in USUARIOS_DEMO]
        return {"exito": True, "mensaje": "", "sesion": self._perfil(), "demo": demo,
                "horarios": availability.horarios_del_dia(),
                "hoy": self._fecha_hoy().isoformat()}

    @_seguro
    def iniciar_sesion(self, usuario, contrasena):
        resultado = iniciar_sesion(self._bd, usuario, contrasena)
        if not resultado["exito"]:
            return {"exito": False, "mensaje": resultado["mensaje"]}
        self._sesion = resultado["sesion"]
        return {"exito": True, "mensaje": "", "sesion": self._perfil()}

    @_seguro
    def crear_cuenta(self, datos):
        resultado = patients.crear_cuenta_paciente(self._bd, datos, self._hoy)
        if not resultado["exito"]:
            return resultado
        self._sesion = iniciar_sesion(self._bd, datos["usuario"], datos["contrasena"])["sesion"]
        return {"exito": True, "mensaje": resultado["mensaje"], "sesion": self._perfil()}

    @_seguro
    def cerrar_sesion(self):
        self._sesion = None
        return {"exito": True, "mensaje": "Sesión cerrada."}

    # -- Catálogos ---------------------------------------------------------------

    @_seguro
    def dentistas(self):
        return {"exito": True, "mensaje": "", "dentistas": [
            {"id": d["id_odontologo"], "nombre": f"{d['nombre']} {d['apellidos']}",
             "especialidad": d["especialidad"] or "Odontología",
             "iniciales": _iniciales(f"{d['nombre']} {d['apellidos']}")}
            for d in self._bd.listar_odontologos()]}

    @_seguro
    def servicios(self):
        resultado = consultar_catalogo(self._bd, self._sesion)
        return {"exito": resultado["exito"], "mensaje": resultado["mensaje"],
                "servicios": resultado["servicios"]}

    @_seguro
    def pacientes(self, busqueda=""):
        resultado = patients.listar_pacientes(self._bd, self._sesion, busqueda)
        for p in resultado["pacientes"]:
            p["iniciales"] = _iniciales(f"{p['nombre']} {p['apellidos']}")
        return resultado

    # -- Citas -------------------------------------------------------------------

    @_seguro
    def disponibilidad(self, id_dentista, fecha, excluir_id_cita=None):
        return availability.consultar_disponibilidad(
            self._bd, self._sesion, id_dentista, fecha, self._hoy, excluir_id_cita)

    @_seguro
    def registrar_cita(self, datos):
        return appointments.registrar_cita(self._bd, self._sesion, datos, self._hoy)

    @_seguro
    def modificar_cita(self, id_cita, cambios):
        return appointments.modificar_cita(self._bd, self._sesion, id_cita, cambios, self._hoy)

    @_seguro
    def cancelar_cita(self, id_cita):
        return appointments.cancelar_cita(self._bd, self._sesion, id_cita)

    @_seguro
    def eliminar_cita(self, id_cita):
        return appointments.eliminar_cita(self._bd, self._sesion, id_cita)

    @_seguro
    def citas(self, filtros=None):
        """Citas según el rol: las propias, las filtradas o la agenda del día."""
        filtros = filtros or {}
        rol = (self._sesion or {}).get("rol")
        if rol == ROL_RECEPCIONISTA:
            return agenda.filtrar_citas(self._bd, self._sesion, filtros.get("fecha"),
                                        filtros.get("dentista"), filtros.get("paciente"))
        if rol == ROL_DENTISTA:
            return agenda.agenda_dentista(self._bd, self._sesion,
                                          filtros.get("fecha") or self._fecha_hoy().isoformat())
        return agenda.mis_citas(self._bd, self._sesion)

    # -- Pacientes (recepción) -----------------------------------------------------

    @_seguro
    def registrar_paciente(self, datos):
        return patients.registrar_paciente(self._bd, self._sesion, datos, self._hoy)

    @_seguro
    def gestionar_acceso(self, id_paciente, usuario, contrasena):
        return patients.gestionar_acceso(self._bd, self._sesion, id_paciente, usuario, contrasena)

    # -- Inicio ----------------------------------------------------------------------

    @_seguro
    def resumen(self):
        """Indicadores de la pantalla de inicio según el rol."""
        if self._sesion is None:
            return {"exito": False, "mensaje": "Error: Debe iniciar sesión."}
        rol = self._sesion["rol"]
        hoy = self._fecha_hoy().isoformat()
        manana = (self._fecha_hoy() + timedelta(days=1)).isoformat()

        if rol == ROL_PACIENTE:
            citas = agenda.mis_citas(self._bd, self._sesion)["citas"]
            proximas = self._futuras(citas, hoy)
            return {"exito": True, "mensaje": "", "proximas": proximas,
                    "indicadores": {"proximas": len(proximas),
                                    "historial": len(citas) - len(proximas),
                                    "total": len(citas)}}

        if rol == ROL_DENTISTA:
            hoy_citas = agenda.agenda_dentista(self._bd, self._sesion, hoy)["citas"]
            manana_citas = agenda.agenda_dentista(self._bd, self._sesion, manana)["citas"]
            return {"exito": True, "mensaje": "", "hoy": hoy_citas,
                    "indicadores": {"hoy": len(hoy_citas), "manana": len(manana_citas),
                                    "libres_hoy": len(availability.horarios_del_dia()) - len(hoy_citas)}}

        todas = self._bd.consultar_citas()
        pacientes = self._bd.listar_pacientes_con_acceso()
        activas_hoy = [c for c in todas if c["fecha"] == hoy and c["estatus"] != ESTATUS_CANCELADA]
        return {"exito": True, "mensaje": "",
                "hoy": activas_hoy,
                "proximas": self._futuras(todas, hoy)[:8],
                "indicadores": {
                    "hoy": len(activas_hoy),
                    "manana": len([c for c in todas if c["fecha"] == manana
                                   and c["estatus"] != ESTATUS_CANCELADA]),
                    "pacientes": len(pacientes),
                    "sin_acceso": len([p for p in pacientes if not p["nombre_usuario"]]),
                }}

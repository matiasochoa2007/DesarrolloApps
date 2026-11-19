"""Orthoimagen Dental - interfaz de consola.

Ejecutar desde la raíz del repositorio:
    py main.py

Une los módulos: el usuario inicia sesión (M1) y ve un menú según su rol.
La interfaz no contiene reglas de negocio: solo pide datos, llama a los
módulos y muestra sus mensajes.
"""

import getpass
from datetime import date

from config import settings
from modules.agenda import agenda_dentista, filtrar_citas, formatear_cita, mis_citas
from modules.appointments import (
    cancelar_cita,
    eliminar_cita,
    modificar_cita,
    registrar_cita,
)
from modules.auth_roles import (
    ROL_DENTISTA,
    ROL_PACIENTE,
    ROL_RECEPCIONISTA,
    iniciar_sesion,
)
from modules.availability import consultar_disponibilidad, fecha_de_manana
from modules.data_access import BaseDatos, ErrorBaseDatos
from modules.demo_data import sembrar_datos_demo
from modules.service_catalog import consultar_catalogo, formatear_servicio

TITULO = "=== Orthoimagen Dental · Sistema de citas ==="


class Consola:
    """Menú de consola. `entrada`, `salida` y `leer_contrasena` se pueden
    sustituir en las pruebas para simular al usuario."""

    def __init__(self, bd, entrada=input, salida=print,
                 leer_contrasena=getpass.getpass):
        self.bd = bd
        self.entrada = entrada
        self.salida = salida
        self.leer_contrasena = leer_contrasena
        self.sesion = None

    # -- Ciclo principal --------------------------------------------------------

    def ejecutar(self):
        self.salida(TITULO)
        while True:
            usuario = self.entrada("\nUsuario (o 'salir'): ").strip()
            if usuario.lower() == "salir":
                self.salida("Hasta luego.")
                return
            contrasena = self.leer_contrasena("Contraseña: ")
            resultado = iniciar_sesion(self.bd, usuario, contrasena)
            if not resultado["exito"]:
                self.salida(resultado["mensaje"])
                continue
            self.sesion = resultado["sesion"]
            self.salida(
                f"Bienvenido(a), {self.sesion['nombre_usuario']} "
                f"(rol: {self.sesion['rol']})."
            )
            self.menu()
            self.sesion = None

    def opciones(self):
        """Opciones del menú según el rol de la sesión: (texto, acción)."""
        rol = self.sesion["rol"]
        opciones = [("Ver catálogo de servicios", self.ver_catalogo)]
        if rol == ROL_PACIENTE:
            opciones += [
                ("Consultar horarios libres de un dentista", self.ver_disponibilidad),
                ("Agendar una cita", self.agendar_cita),
                ("Ver mis citas", self.ver_mis_citas),
                ("Modificar una de mis citas", self.modificar),
                ("Cancelar una de mis citas", self.cancelar),
            ]
        elif rol == ROL_RECEPCIONISTA:
            opciones += [
                ("Consultar disponibilidad de un dentista", self.ver_disponibilidad),
                ("Registrar una cita para un paciente", self.agendar_cita),
                ("Ver y filtrar citas", self.ver_citas_filtradas),
                ("Modificar una cita", self.modificar),
                ("Cancelar una cita", self.cancelar),
                ("Eliminar una cita", self.eliminar),
            ]
        elif rol == ROL_DENTISTA:
            opciones += [("Ver mi agenda del día", self.ver_agenda)]
        return opciones

    def menu(self):
        while True:
            opciones = self.opciones()
            self.salida("\n--- Menú ---")
            for numero, (texto, _) in enumerate(opciones, start=1):
                self.salida(f"{numero}. {texto}")
            self.salida("0. Cerrar sesión")
            eleccion = self.entrada("Opción: ").strip()
            if eleccion == "0":
                self.salida("Sesión cerrada.")
                return
            if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(opciones):
                self.salida("Error: Opción no válida. Escriba el número de una opción.")
                continue
            opciones[int(eleccion) - 1][1]()

    # -- Acciones -------------------------------------------------------------

    def mostrar(self, resultado):
        """Muestra el mensaje de un resultado si lo trae."""
        if resultado.get("mensaje"):
            self.salida(resultado["mensaje"])

    def ver_catalogo(self):
        resultado = consultar_catalogo(self.bd, self.sesion)
        self.mostrar(resultado)
        for servicio in resultado["servicios"]:
            self.salida(formatear_servicio(servicio))

    # -- Ayudas para capturar datos ---------------------------------------------

    def preguntar(self, texto):
        return self.entrada(texto).strip()

    def elegir_dentista(self):
        try:
            dentistas = self.bd.listar_odontologos()
        except ErrorBaseDatos as error:
            self.salida(error.mensaje)
            return None
        self.salida("Dentistas:")
        for d in dentistas:
            especialidad = f" · {d['especialidad']}" if d["especialidad"] else ""
            self.salida(f"[{d['id_odontologo']}] {d['nombre']} {d['apellidos']}{especialidad}")
        return self.preguntar("Número del dentista: ")

    def elegir_paciente(self):
        try:
            pacientes = self.bd.listar_pacientes()
        except ErrorBaseDatos as error:
            self.salida(error.mensaje)
            return None
        self.salida("Pacientes:")
        for p in pacientes:
            self.salida(f"[{p['id_paciente']}] {p['nombre']} {p['apellidos']} · {p['telefono']}")
        return self.preguntar("Número del paciente: ")

    def pedir_fecha(self):
        return self.preguntar(f"Fecha (AAAA-MM-DD, p. ej. {fecha_de_manana()}): ")

    # -- Disponibilidad y registro (Incremento 3) --------------------------------

    def ver_disponibilidad(self):
        id_odontologo = self.elegir_dentista()
        if id_odontologo is None:
            return
        resultado = consultar_disponibilidad(self.bd, self.sesion, id_odontologo,
                                             self.pedir_fecha())
        self.mostrar(resultado)
        if resultado["libres"]:
            self.salida("Horarios libres: " + ", ".join(resultado["libres"]))
        if resultado["ocupados"]:
            self.salida("Horarios ocupados: " + ", ".join(resultado["ocupados"]))

    def agendar_cita(self):
        datos = {}
        if self.sesion["rol"] == ROL_RECEPCIONISTA:
            datos["paciente"] = self.elegir_paciente()
        datos["dentista"] = self.elegir_dentista()
        datos["fecha"] = self.pedir_fecha()
        datos["hora"] = self.preguntar("Hora (HH:MM): ")
        self.ver_catalogo()
        datos["servicio"] = self.preguntar("Número del servicio: ")
        datos["motivo"] = self.preguntar("Motivo (opcional): ")
        self.mostrar(registrar_cita(self.bd, self.sesion, datos))

    # -- Consultas y cambios (Incremento 4) ---------------------------------------

    def mostrar_citas(self, resultado):
        self.mostrar(resultado)
        for cita in resultado["citas"]:
            self.salida(formatear_cita(cita))

    def ver_mis_citas(self):
        self.mostrar_citas(mis_citas(self.bd, self.sesion))

    def ver_citas_filtradas(self):
        self.salida("Deje vacío el filtro que no quiera aplicar.")
        fecha = self.preguntar("Día (AAAA-MM-DD): ")
        dentista = self.preguntar("Número del dentista: ")
        paciente = self.preguntar("Número del paciente: ")
        self.mostrar_citas(filtrar_citas(self.bd, self.sesion, fecha, dentista, paciente))

    def ver_agenda(self):
        fecha = self.preguntar(f"Día (AAAA-MM-DD, Enter para hoy {date.today().isoformat()}): ")
        self.mostrar_citas(agenda_dentista(self.bd, self.sesion,
                                           fecha or date.today().isoformat()))

    def pedir_folio(self):
        if self.sesion["rol"] == ROL_PACIENTE:
            self.ver_mis_citas()
        return self.preguntar("Folio de la cita: ")

    def modificar(self):
        id_cita = self.pedir_folio()
        self.salida("Escriba el nuevo valor o presione Enter para conservar el actual.")
        cambios = {}
        if self.sesion["rol"] == ROL_RECEPCIONISTA:
            cambios["dentista"] = self.preguntar("Nuevo dentista (número): ")
        cambios["fecha"] = self.preguntar("Nueva fecha (AAAA-MM-DD): ")
        cambios["hora"] = self.preguntar("Nueva hora (HH:MM): ")
        cambios["servicio"] = self.preguntar("Nuevo servicio (número): ")
        cambios["motivo"] = self.preguntar("Nuevo motivo: ")
        cambios = {campo: valor for campo, valor in cambios.items() if valor}
        self.mostrar(modificar_cita(self.bd, self.sesion, id_cita, cambios))

    def cancelar(self):
        self.mostrar(cancelar_cita(self.bd, self.sesion, self.pedir_folio()))

    def eliminar(self):
        id_cita = self.pedir_folio()
        confirmacion = self.preguntar(
            f"¿Eliminar definitivamente la cita {id_cita}? No se puede deshacer (s/n): "
        )
        if confirmacion.lower() != "s":
            self.salida("Eliminación cancelada; la cita no se modificó.")
            return
        self.mostrar(eliminar_cita(self.bd, self.sesion, id_cita))


def main():
    try:
        settings.RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
        bd = BaseDatos(settings.RUTA_BD)
        bd.inicializar()
        if sembrar_datos_demo(bd):
            print("Se cargaron los datos de demostración (ver README).")
    except (ErrorBaseDatos, OSError) as error:
        print(getattr(error, "mensaje", str(error)))
        return 1
    try:
        Consola(bd).ejecutar()
    except (KeyboardInterrupt, EOFError):
        print("\nHasta luego.")
    finally:
        bd.cerrar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

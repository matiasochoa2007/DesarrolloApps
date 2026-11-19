"""Orthoimagen Dental - interfaz de consola.

Ejecutar desde la raíz del repositorio:
    py main.py

Une los módulos: el usuario inicia sesión (M1) y ve un menú según su rol.
La interfaz no contiene reglas de negocio: solo pide datos, llama a los
módulos y muestra sus mensajes.
"""

import getpass

from config import settings
from modules.auth_roles import iniciar_sesion
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
        return [("Ver catálogo de servicios", self.ver_catalogo)]

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

"""Pruebas de extremo a extremo de la app de escritorio (app_escritorio.py).

Crean la ventana oculta, llenan los campos como lo haría el usuario y
revisan el resultado en la base y en la barra de estado.

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_app_escritorio -v
"""

import tkinter as tk
import unittest
from datetime import date, timedelta

from modules.demo_data import USUARIOS_DEMO, sembrar_datos_demo
from tests.utilidades import BaseTemporal

try:
    from app_escritorio import App, DialogoModificar, mover_fecha

    _raiz = tk.Tk()
    _raiz.destroy()
    HAY_PANTALLA = True
except tk.TclError:  # Entorno sin pantalla (por ejemplo, un servidor de CI)
    HAY_PANTALLA = False

CLAVES = {usuario: clave for usuario, clave, _, _ in USUARIOS_DEMO}
MANANA = (date.today() + timedelta(days=1)).isoformat()


@unittest.skipUnless(HAY_PANTALLA, "Se necesita una pantalla para tkinter")
class PruebasAppEscritorio(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        sembrar_datos_demo(self.temp.bd)
        self.app = App(self.temp.bd)
        self.app.withdraw()
        self.app.confirmar = lambda titulo, texto: True

    def tearDown(self):
        self.app.destroy()
        self.temp.limpiar()

    def entrar(self, usuario, clave=None):
        login = self.app.pantalla
        login.usuario.set(usuario)
        login.contrasena.set(CLAVES[usuario] if clave is None else clave)
        login.iniciar()
        self.app.update_idletasks()
        return self.app.pantalla

    def estado(self, principal):
        return principal.estado.cget("text")

    def agendar(self, principal, hora="16:00", indice_paciente=None):
        pestana = principal.pestana_agendar
        if indice_paciente is not None:
            pestana.combo_paciente.current(indice_paciente)
        pestana.combo_dentista.current(0)
        pestana.fecha.set(MANANA)
        pestana.ver_horarios()
        horarios = list(pestana.lista_horarios.get(0, "end"))
        pestana.lista_horarios.selection_set(horarios.index(hora))
        pestana.combo_servicio.current(0)
        pestana.confirmar()
        return self.estado(principal)

    def test_login_incorrecto_muestra_mensaje(self):
        pantalla = self.entrar("paciente01", "mala")
        self.assertIn("incorrectos", pantalla.mensaje.cget("text"))

    def test_pestanas_segun_rol(self):
        for usuario, esperadas in (
                ("paciente01", ["Agendar cita", "Mis citas", "Catálogo de servicios"]),
                ("recepcion01", ["Registrar cita", "Citas", "Catálogo de servicios"]),
                ("dentista01", ["Mi agenda", "Catálogo de servicios"])):
            principal = self.entrar(usuario)
            pestanas = [principal.pestanas.tab(t, "text") for t in principal.pestanas.tabs()]
            self.assertEqual(pestanas, esperadas, usuario)
            self.app.mostrar_login()

    def test_catalogo_muestra_servicios(self):
        principal = self.entrar("dentista01")
        self.assertEqual(len(principal.pestana_catalogo.arbol.get_children()), 4)

    def test_paciente_agenda_en_cinco_pasos_y_ve_su_cita(self):
        principal = self.entrar("paciente01")
        mensaje = self.agendar(principal)
        self.assertIn("Cita registrada", mensaje)
        filas = principal.pestana_citas.arbol.get_children()
        self.assertEqual(len(filas), 1)
        # El horario ya no aparece como libre.
        self.assertNotIn("16:00", principal.pestana_agendar.lista_horarios.get(0, "end"))

    def test_confirmar_sin_horario_nombra_el_campo(self):
        principal = self.entrar("paciente01")
        pestana = principal.pestana_agendar
        pestana.combo_dentista.current(0)
        pestana.combo_servicio.current(0)
        pestana.confirmar()
        self.assertIn("'hora'", self.estado(principal))

    def test_recepcion_registra_modifica_cancela_y_elimina(self):
        principal = self.entrar("recepcion01")
        self.assertIn("Cita registrada", self.agendar(principal, indice_paciente=0))
        citas = principal.pestana_citas
        id_cita = citas.arbol.get_children()[0]

        citas.arbol.selection_set(id_cita)
        citas.modificar()
        dialogo = next(w for w in citas.winfo_children() if isinstance(w, DialogoModificar))
        dialogo.combo_hora.set("17:00")
        dialogo.guardar()
        self.assertIn("Reprogramada", self.estado(principal))

        citas.arbol.selection_set(id_cita)
        citas.cancelar()
        self.assertIn("cancelada", self.estado(principal))
        self.assertEqual(self.temp.bd.obtener_cita(int(id_cita))["estatus"], "Cancelada")

        citas.arbol.selection_set(id_cita)
        citas.eliminar()
        self.assertIn("eliminada definitivamente", self.estado(principal))
        self.assertIsNone(self.temp.bd.obtener_cita(int(id_cita)))

    def test_eliminar_requiere_confirmacion(self):
        principal = self.entrar("recepcion01")
        self.agendar(principal, indice_paciente=0)
        citas = principal.pestana_citas
        id_cita = citas.arbol.get_children()[0]
        self.app.confirmar = lambda titulo, texto: False
        citas.arbol.selection_set(id_cita)
        citas.eliminar()
        self.assertIsNotNone(self.temp.bd.obtener_cita(int(id_cita)))

    def test_dentista_ve_su_agenda(self):
        self.agendar(self.entrar("paciente01"))
        self.app.mostrar_login()
        principal = self.entrar("dentista01")
        agenda = principal.pestana_citas
        agenda.fecha.set(MANANA)
        agenda.cargar()
        self.assertEqual(len(agenda.arbol.get_children()), 1)

    def test_mover_fecha(self):
        self.assertEqual(mover_fecha("2030-12-31", 1), "2031-01-01")
        self.assertEqual(mover_fecha("2030-03-01", -1), "2030-02-28")


if __name__ == "__main__":
    unittest.main()

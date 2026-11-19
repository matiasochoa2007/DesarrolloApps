"""Pruebas de extremo a extremo de la interfaz (interfaz/api.py).

Recorren los mismos caminos que sigue la ventana de la aplicación, sin
necesidad de abrirla.

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_api -v
"""

import json
import unittest
from datetime import date

from interfaz.api import ApiOrthoimagen
from modules.demo_data import USUARIOS_DEMO, sembrar_datos_demo
from tests.utilidades import BaseTemporal

HOY = date(2030, 3, 1)
MANANA = "2030-03-02"
CLAVES = {u: c for u, c, _, _ in USUARIOS_DEMO}


class EscenarioApi(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        sembrar_datos_demo(self.temp.bd)
        self.api = ApiOrthoimagen(self.temp.bd, hoy=HOY)

    def tearDown(self):
        self.temp.limpiar()

    def entrar(self, usuario):
        resultado = self.api.iniciar_sesion(usuario, CLAVES[usuario])
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        return resultado["sesion"]

    def agendar(self, hora="10:00", **extra):
        datos = {"fecha": MANANA, "hora": hora, "dentista": 1, "servicio": 2}
        datos.update(extra)
        return self.api.registrar_cita(datos)


class PruebasSesion(EscenarioApi):
    def test_estado_inicial_sin_sesion(self):
        estado = self.api.estado()
        self.assertIsNone(estado["sesion"])
        self.assertEqual(len(estado["demo"]), 5)
        self.assertEqual(estado["horarios"][0], "09:00")
        json.dumps(estado)  # todo debe ser serializable para la interfaz

    def test_perfil_por_rol(self):
        self.assertEqual(self.entrar("paciente01")["nombre"], "Ana Pérez Soto")
        self.assertEqual(self.entrar("dentista01")["nombre"], "Dr(a). Laura Peña Núñez")
        perfil = self.entrar("recepcion01")
        self.assertEqual((perfil["nombre"], perfil["iniciales"]), ("Recepción", "R"))

    def test_login_incorrecto_y_cerrar_sesion(self):
        self.assertIn("incorrectos", self.api.iniciar_sesion("paciente01", "x")["mensaje"])
        self.entrar("paciente01")
        self.api.cerrar_sesion()
        self.assertIsNone(self.api.estado()["sesion"])
        self.assertFalse(self.api.registrar_cita({})["exito"])

    def test_sin_modo_demo_no_expone_usuarios(self):
        api = ApiOrthoimagen(self.temp.bd, modo_demo=False)
        self.assertEqual(api.estado()["demo"], [])


class PruebasClienteNuevo(EscenarioApi):
    def test_cliente_nuevo_crea_cuenta_y_agenda_su_primera_cita(self):
        resultado = self.api.crear_cuenta({
            "nombre": "Sofía", "apellidos": "Lara", "telefono": "4779990000",
            "usuario": "sofia.lara", "contrasena": "Sonrisa2030",
            "confirmacion": "Sonrisa2030"})
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertEqual(resultado["sesion"]["nombre"], "Sofía Lara")
        cita = self.agendar()
        self.assertTrue(cita["exito"], cita["mensaje"])
        resumen = self.api.resumen()
        self.assertEqual(resumen["indicadores"]["proximas"], 1)

    def test_error_al_crear_cuenta_no_inicia_sesion(self):
        resultado = self.api.crear_cuenta({"nombre": "Sofía"})
        self.assertFalse(resultado["exito"])
        self.assertIsNone(self.api.estado()["sesion"])


class PruebasRecepcionApi(EscenarioApi):
    def test_recepcion_registra_paciente_y_le_agenda(self):
        self.entrar("recepcion01")
        nuevo = self.api.registrar_paciente({"nombre": "Hugo", "apellidos": "Mena",
                                             "telefono": "4770001111"})
        self.assertTrue(nuevo["exito"], nuevo["mensaje"])
        cita = self.agendar(paciente=nuevo["id_paciente"])
        self.assertTrue(cita["exito"], cita["mensaje"])
        pacientes = self.api.pacientes("mena")["pacientes"]
        self.assertEqual(pacientes[0]["iniciales"], "HM")
        acceso = self.api.gestionar_acceso(nuevo["id_paciente"], "hugo.mena", "Dientes2030")
        self.assertTrue(acceso["exito"], acceso["mensaje"])

    def test_resumen_y_filtros(self):
        self.entrar("recepcion01")
        self.agendar(paciente=1)
        self.agendar(hora="11:00", paciente=2)
        resumen = self.api.resumen()
        self.assertEqual(resumen["indicadores"]["manana"], 2)
        self.assertEqual(resumen["indicadores"]["pacientes"], 2)
        self.assertEqual(len(self.api.citas({"fecha": MANANA, "dentista": 1})["citas"]), 2)
        self.assertEqual(len(self.api.citas({"paciente": 2})["citas"]), 1)

    def test_modificar_con_disponibilidad_que_excluye_la_cita(self):
        self.entrar("recepcion01")
        id_cita = self.agendar(paciente=1)["id_cita"]
        libres = self.api.disponibilidad(1, MANANA, id_cita)["libres"]
        self.assertIn("10:00", libres)
        resultado = self.api.modificar_cita(id_cita, {"hora": "12:00"})
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertTrue(self.api.cancelar_cita(id_cita)["exito"])
        self.assertTrue(self.api.eliminar_cita(id_cita)["exito"])


class PruebasDentistaApi(EscenarioApi):
    def test_dentista_ve_su_agenda(self):
        self.entrar("paciente01")
        self.agendar()
        self.entrar("dentista01")
        self.assertEqual(len(self.api.citas({"fecha": MANANA})["citas"]), 1)
        self.assertEqual(self.api.resumen()["indicadores"]["manana"], 1)


if __name__ == "__main__":
    unittest.main()

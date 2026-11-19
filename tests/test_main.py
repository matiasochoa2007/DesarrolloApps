"""Pruebas de extremo a extremo de la consola (main.py).

Simulan lo que escribe el usuario y revisan lo que el sistema muestra.

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_main -v
"""

import unittest
from datetime import date, timedelta

from main import Consola
from modules.demo_data import USUARIOS_DEMO, sembrar_datos_demo
from tests.utilidades import BaseTemporal

CLAVES = {usuario: clave for usuario, clave, _, _ in USUARIOS_DEMO}


def simular(bd, pasos):
    """Ejecuta la consola con una lista de respuestas.

    Cada contraseña se toma de la misma lista. Devuelve el texto mostrado.
    """
    respuestas = iter(pasos)
    mostrado = []
    consola = Consola(
        bd,
        entrada=lambda _: next(respuestas),
        salida=lambda texto="": mostrado.append(str(texto)),
        leer_contrasena=lambda _: next(respuestas),
    )
    consola.ejecutar()
    return "\n".join(mostrado)


class PruebasDatosDemo(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_sembrar_solo_una_vez(self):
        self.assertTrue(sembrar_datos_demo(self.temp.bd))
        self.assertFalse(sembrar_datos_demo(self.temp.bd))
        self.assertEqual(self.temp.bd.contar_usuarios(), len(USUARIOS_DEMO))


class PruebasConsolaIncremento2(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        sembrar_datos_demo(self.temp.bd)

    def tearDown(self):
        self.temp.limpiar()

    def test_login_ver_catalogo_y_salir(self):
        texto = simular(self.temp.bd, [
            "paciente01", CLAVES["paciente01"], "1", "0", "salir",
        ])
        self.assertIn("rol: paciente", texto)
        self.assertIn("Limpieza dental", texto)
        self.assertIn("Sesión cerrada.", texto)

    def test_login_incorrecto_muestra_error_y_permite_reintentar(self):
        texto = simular(self.temp.bd, [
            "paciente01", "mala", "recepcion01", CLAVES["recepcion01"], "0", "salir",
        ])
        self.assertIn("Usuario o contraseña incorrectos", texto)
        self.assertIn("rol: recepcionista", texto)

    def test_opcion_invalida(self):
        texto = simular(self.temp.bd, [
            "dentista01", CLAVES["dentista01"], "99", "abc", "0", "salir",
        ])
        self.assertEqual(texto.count("Opción no válida"), 2)


MANANA = (date.today() + timedelta(days=1)).isoformat()


class PruebasConsolaIncremento3(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        sembrar_datos_demo(self.temp.bd)

    def tearDown(self):
        self.temp.limpiar()

    def test_paciente_consulta_y_agenda_su_cita(self):
        texto = simular(self.temp.bd, [
            "paciente01", CLAVES["paciente01"],
            "2", "1", MANANA,                                  # disponibilidad
            "3", "1", MANANA, "17:00", "2", "Limpieza",        # agendar
            "0", "salir",
        ])
        self.assertIn("Horarios libres:", texto)
        self.assertIn("Cita registrada", texto)
        self.assertIn("Limpieza dental", texto)

    def test_recepcionista_registra_y_detecta_horario_ocupado(self):
        texto = simular(self.temp.bd, [
            "recepcion01", CLAVES["recepcion01"],
            "3", "1", "1", MANANA, "17:00", "1", "",
            "3", "2", "1", MANANA, "17:00", "1", "",
            "2", "1", MANANA,
            "0", "salir",
        ])
        self.assertEqual(texto.count("Cita registrada"), 1)
        self.assertIn("no está disponible", texto)
        self.assertIn("Horarios ocupados: 17:00", texto)

    def test_dentista_no_ve_opciones_de_registro(self):
        texto = simular(self.temp.bd, ["dentista01", CLAVES["dentista01"], "0", "salir"])
        self.assertNotIn("Agendar una cita", texto)
        self.assertNotIn("Registrar una cita", texto)


if __name__ == "__main__":
    unittest.main()

"""Pruebas de M5 Catálogo de servicios (RF-08, HU-14).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_service_catalog -v
"""

import unittest

from modules.data_access import BaseDatos
from modules.service_catalog import (
    MENSAJE_CATALOGO_VACIO,
    consultar_catalogo,
    formatear_servicio,
)
from tests.utilidades import BaseTemporal, ruta_no_disponible

SESION_PACIENTE = {"rol": "paciente", "id_paciente": 1}


class PruebasCatalogo(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_ca42_catalogo_con_servicios(self):
        self.temp.bd.insertar_servicio("Limpieza dental", 45, precio=850.0)
        self.temp.bd.insertar_servicio("Extracción simple", 60, precio=1200.0)
        resultado = consultar_catalogo(self.temp.bd, SESION_PACIENTE)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["mensaje"], "")
        nombres = [s["nombre"] for s in resultado["servicios"]]
        self.assertEqual(nombres, ["Extracción simple", "Limpieza dental"])

    def test_ca43_catalogo_vacio_muestra_aviso(self):
        resultado = consultar_catalogo(self.temp.bd, SESION_PACIENTE)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["servicios"], [])
        self.assertEqual(resultado["mensaje"], MENSAJE_CATALOGO_VACIO)

    def test_ca44_base_no_disponible(self):
        resultado = consultar_catalogo(BaseDatos(ruta_no_disponible()), SESION_PACIENTE)
        self.assertFalse(resultado["exito"])
        self.assertIn("No se pudo acceder a la base de datos", resultado["mensaje"])

    def test_sin_sesion_no_consulta(self):
        resultado = consultar_catalogo(self.temp.bd, None)
        self.assertFalse(resultado["exito"])
        self.assertIn("iniciar sesión", resultado["mensaje"])

    def test_formatear_servicio(self):
        texto = formatear_servicio({"id_servicio": 3, "nombre": "Limpieza dental",
                                    "duracion_min": 45, "precio": 850.0})
        self.assertEqual(texto, "[3] Limpieza dental · 45 min · $850.00 MXN")
        sin_precio = formatear_servicio({"id_servicio": 4, "nombre": "Valoración",
                                         "duracion_min": 30, "precio": None})
        self.assertIn("precio a consultar", sin_precio)


if __name__ == "__main__":
    unittest.main()

"""Pruebas de M7 Acceso a datos (RF-09, HU-17).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_data_access -v
"""

import unittest

from modules.data_access import TABLAS, BaseDatos, ErrorBaseDatos
from tests.utilidades import BaseTemporal, ruta_no_disponible


class PruebasEsquema(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_crea_las_cinco_tablas(self):
        self.assertEqual(sorted(self.temp.bd.tablas()), sorted(TABLAS))

    def test_inicializar_dos_veces_no_falla(self):
        self.temp.bd.inicializar()
        self.assertEqual(len(self.temp.bd.tablas()), 5)

    def test_llaves_foraneas_activas(self):
        fila = self.temp.bd._consultar_uno("PRAGMA foreign_keys")
        self.assertEqual(fila["foreign_keys"], 1)


class PruebasBaseNoDisponible(unittest.TestCase):
    def test_ca53_ruta_invalida_lanza_error_con_mensaje_claro(self):
        bd = BaseDatos(ruta_no_disponible())
        with self.assertRaises(ErrorBaseDatos) as contexto:
            bd.inicializar()
        self.assertIn("No se pudo acceder a la base de datos", contexto.exception.mensaje)


if __name__ == "__main__":
    unittest.main()

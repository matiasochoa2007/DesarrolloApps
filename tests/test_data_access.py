"""Pruebas de M7 Acceso a datos (RF-09, HU-17).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_data_access -v
"""

import unittest

from modules.data_access import TABLAS, BaseDatos, ErrorBaseDatos, ErrorIntegridad
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


class PruebasGuardarYLeer(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_ca51_guardar_cerrar_reabrir_y_leer(self):
        id_paciente = self.temp.bd.insertar_paciente(
            "María Fernanda", "López Ramírez", "4771234567",
            correo="maria.lopez@correo.com", fecha_nacimiento="1998-05-21",
        )
        bd = self.temp.reabrir()
        paciente = bd.obtener_paciente(id_paciente)
        self.assertEqual(paciente["nombre"], "María Fernanda")
        self.assertEqual(paciente["telefono"], "4771234567")

    def test_ca52_varias_filas(self):
        bd = self.temp.bd
        bd.insertar_servicio("Limpieza dental", 45, precio=850.0)
        bd.insertar_servicio("Ortodoncia - revisión", 30, precio=600.0)
        bd.insertar_servicio("Radiografía panorámica", 20, precio=450.0)
        bd = self.temp.reabrir()
        nombres = [s["nombre"] for s in bd.listar_servicios()]
        self.assertEqual(len(nombres), 3)
        self.assertEqual(nombres, sorted(nombres))

    def test_odontologos_activos_e_inactivos(self):
        bd = self.temp.bd
        bd.insertar_odontologo("Laura", "Peña", "Ortodoncia")
        bd.insertar_odontologo("Jorge", "Ruiz", activo=False)
        self.assertEqual(len(bd.listar_odontologos()), 1)
        self.assertEqual(len(bd.listar_odontologos(solo_activos=False)), 2)

    def test_usuario_guardado_con_rol(self):
        bd = self.temp.bd
        bd.insertar_usuario("recepcion01", "hash", "recepcionista")
        usuario = bd.obtener_usuario_por_nombre("recepcion01")
        self.assertEqual(usuario["rol"], "recepcionista")
        self.assertEqual(bd.contar_usuarios(), 1)

    def test_lectura_inexistente_devuelve_none(self):
        self.assertIsNone(self.temp.bd.obtener_paciente(999))
        self.assertIsNone(self.temp.bd.obtener_usuario_por_nombre("nadie"))


class PruebasIntegridad(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_usuario_duplicado_lanza_error_integridad(self):
        self.temp.bd.insertar_usuario("paciente01", "hash", "paciente")
        with self.assertRaises(ErrorIntegridad):
            self.temp.bd.insertar_usuario("paciente01", "otro", "paciente")

    def test_rol_invalido_lanza_error_integridad(self):
        with self.assertRaises(ErrorIntegridad):
            self.temp.bd.insertar_usuario("admin", "hash", "administrador")

    def test_referencia_inexistente_lanza_error_integridad(self):
        with self.assertRaises(ErrorIntegridad):
            self.temp.bd.insertar_usuario("p", "hash", "paciente", id_paciente=99)


class PruebasBaseNoDisponible(unittest.TestCase):
    def test_ca53_ruta_invalida_lanza_error_con_mensaje_claro(self):
        bd = BaseDatos(ruta_no_disponible())
        with self.assertRaises(ErrorBaseDatos) as contexto:
            bd.inicializar()
        self.assertIn("No se pudo acceder a la base de datos", contexto.exception.mensaje)

    def test_ca53_lectura_con_base_no_disponible(self):
        bd = BaseDatos(ruta_no_disponible())
        with self.assertRaises(ErrorBaseDatos):
            bd.listar_servicios()


if __name__ == "__main__":
    unittest.main()

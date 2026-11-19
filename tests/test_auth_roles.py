"""Pruebas de M1 Autenticación y roles (RF-11, HU-16).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_auth_roles -v
"""

import unittest

from modules.auth_roles import (
    MENSAJE_CREDENCIALES_INCORRECTAS,
    MENSAJE_CREDENCIALES_VACIAS,
    PERMISOS,
    ROLES,
    generar_hash,
    iniciar_sesion,
    registrar_usuario,
    verificar_contrasena,
    verificar_permiso,
)
from modules.data_access import BaseDatos
from tests.utilidades import BaseTemporal, ruta_no_disponible

CLAVE = "Prueba-2026"


class PruebasHash(unittest.TestCase):
    def test_hash_no_guarda_texto_plano(self):
        guardado = generar_hash(CLAVE, iteraciones=1000)
        self.assertNotIn(CLAVE, guardado)
        self.assertTrue(guardado.startswith("pbkdf2_sha256$1000$"))

    def test_misma_clave_genera_hash_distinto_por_la_sal(self):
        self.assertNotEqual(generar_hash(CLAVE, 1000), generar_hash(CLAVE, 1000))

    def test_verificar_contrasena(self):
        guardado = generar_hash(CLAVE, iteraciones=1000)
        self.assertTrue(verificar_contrasena(CLAVE, guardado))
        self.assertFalse(verificar_contrasena("otra", guardado))
        self.assertFalse(verificar_contrasena(CLAVE, "formato-invalido"))


class PruebasInicioSesion(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.temp.bd
        self.id_paciente = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.id_odontologo = bd.insertar_odontologo("Laura", "Peña")
        registrar_usuario(bd, "recepcion01", CLAVE, "recepcionista")
        registrar_usuario(bd, "paciente01", CLAVE, "paciente",
                          id_paciente=self.id_paciente)
        registrar_usuario(bd, "dentista01", CLAVE, "dentista",
                          id_odontologo=self.id_odontologo)

    def tearDown(self):
        self.temp.limpiar()

    def test_ca48_credenciales_correctas_devuelven_rol(self):
        for usuario, rol in (("recepcion01", "recepcionista"),
                             ("paciente01", "paciente"),
                             ("dentista01", "dentista")):
            resultado = iniciar_sesion(self.temp.bd, usuario, CLAVE)
            self.assertTrue(resultado["exito"], usuario)
            self.assertEqual(resultado["sesion"]["rol"], rol)

    def test_ca48_sesion_del_paciente_incluye_su_id(self):
        sesion = iniciar_sesion(self.temp.bd, "paciente01", CLAVE)["sesion"]
        self.assertEqual(sesion["id_paciente"], self.id_paciente)
        self.assertIsNone(sesion["id_odontologo"])

    def test_ca50_contrasena_incorrecta(self):
        resultado = iniciar_sesion(self.temp.bd, "paciente01", "mala")
        self.assertFalse(resultado["exito"])
        self.assertIsNone(resultado["sesion"])
        self.assertEqual(resultado["mensaje"], MENSAJE_CREDENCIALES_INCORRECTAS)

    def test_ca50_usuario_inexistente_mismo_mensaje(self):
        resultado = iniciar_sesion(self.temp.bd, "nadie", CLAVE)
        self.assertEqual(resultado["mensaje"], MENSAJE_CREDENCIALES_INCORRECTAS)

    def test_ca50_credenciales_vacias(self):
        for usuario, clave in (("", CLAVE), ("paciente01", "   "), (None, None)):
            resultado = iniciar_sesion(self.temp.bd, usuario, clave)
            self.assertFalse(resultado["exito"])
            self.assertEqual(resultado["mensaje"], MENSAJE_CREDENCIALES_VACIAS)

    def test_base_no_disponible_al_iniciar_sesion(self):
        resultado = iniciar_sesion(BaseDatos(ruta_no_disponible()), "a", "b")
        self.assertFalse(resultado["exito"])
        self.assertIn("base de datos", resultado["mensaje"])


class PruebasRegistroUsuario(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()

    def tearDown(self):
        self.temp.limpiar()

    def test_usuario_duplicado(self):
        registrar_usuario(self.temp.bd, "recepcion01", CLAVE, "recepcionista")
        resultado = registrar_usuario(self.temp.bd, "recepcion01", CLAVE,
                                      "recepcionista")
        self.assertFalse(resultado["exito"])
        self.assertIn("ya existe", resultado["mensaje"])

    def test_rol_invalido(self):
        resultado = registrar_usuario(self.temp.bd, "admin", CLAVE, "administrador")
        self.assertFalse(resultado["exito"])
        self.assertIn("administrador", resultado["mensaje"])

    def test_paciente_sin_vinculo(self):
        resultado = registrar_usuario(self.temp.bd, "p", CLAVE, "paciente")
        self.assertFalse(resultado["exito"])

    def test_dentista_sin_vinculo(self):
        resultado = registrar_usuario(self.temp.bd, "d", CLAVE, "dentista")
        self.assertFalse(resultado["exito"])


class PruebasPermisos(unittest.TestCase):
    def test_ca49_paciente_no_puede_usar_funcion_de_recepcion(self):
        sesion = {"rol": "paciente"}
        for accion in ("registrar_cita_para_paciente", "filtrar_citas",
                       "eliminar_cita"):
            resultado = verificar_permiso(sesion, accion)
            self.assertFalse(resultado["exito"], accion)
            self.assertIn("paciente", resultado["mensaje"])

    def test_recepcionista_si_puede_usar_funciones_de_recepcion(self):
        sesion = {"rol": "recepcionista"}
        self.assertTrue(verificar_permiso(sesion, "eliminar_cita")["exito"])
        self.assertTrue(verificar_permiso(sesion, "filtrar_citas")["exito"])

    def test_todos_los_roles_consultan_catalogo(self):
        for rol in ROLES:
            self.assertTrue(verificar_permiso({"rol": rol}, "consultar_catalogo")["exito"])

    def test_sin_sesion_o_accion_desconocida(self):
        self.assertFalse(verificar_permiso(None, "consultar_catalogo")["exito"])
        self.assertFalse(verificar_permiso({"rol": "recepcionista"}, "x")["exito"])

    def test_solo_existen_los_tres_roles(self):
        roles_usados = set().union(*PERMISOS.values())
        self.assertEqual(roles_usados, set(ROLES))


if __name__ == "__main__":
    unittest.main()

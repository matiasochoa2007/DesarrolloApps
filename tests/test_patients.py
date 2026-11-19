"""Pruebas de M8 Registro de pacientes y accesos (extensión v1.1).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_patients -v
"""

import unittest
from datetime import date

from modules.auth_roles import iniciar_sesion
from modules.data_access import BaseDatos
from modules.patients import (
    MENSAJE_CONTRASENA_DEBIL,
    MENSAJE_CONTRASENAS_DISTINTAS,
    MENSAJE_TELEFONO_INVALIDO,
    MENSAJE_USUARIO_INVALIDO,
    crear_cuenta_paciente,
    gestionar_acceso,
    listar_pacientes,
    normalizar_telefono,
    registrar_paciente,
    validar_datos_paciente,
)
from tests.utilidades import BaseTemporal, ruta_no_disponible

HOY = date(2030, 3, 1)
RECEPCION = {"rol": "recepcionista"}


def nuevo(**cambios):
    datos = {"nombre": "Sofía", "apellidos": "Lara Ríos", "telefono": "477 123 4567",
             "correo": "sofia@correo.com", "fecha_nacimiento": "1995-06-10",
             "usuario": "sofia.lara", "contrasena": "Sonrisa2030",
             "confirmacion": "Sonrisa2030"}
    datos.update(cambios)
    return datos


class PruebasValidacion(unittest.TestCase):
    def test_datos_validos(self):
        self.assertEqual(validar_datos_paciente(nuevo(), HOY), "")

    def test_campos_obligatorios_con_mensaje_de_m6(self):
        self.assertEqual(
            validar_datos_paciente({"nombre": "Ana"}, HOY),
            "Error: Los siguientes campos son obligatorios y están vacíos: apellidos, telefono.",
        )

    def test_telefono_de_10_digitos(self):
        self.assertEqual(normalizar_telefono("(477) 123-45 67"), "4771234567")
        for malo in ("477123", "47712345678", "477-ABC-4567"):
            self.assertEqual(validar_datos_paciente(nuevo(telefono=malo), HOY),
                             MENSAJE_TELEFONO_INVALIDO)

    def test_correo_y_nacimiento_opcionales_pero_validados(self):
        self.assertEqual(validar_datos_paciente(nuevo(correo="", fecha_nacimiento=""), HOY), "")
        self.assertIn("no es válido", validar_datos_paciente(nuevo(correo="sofia@"), HOY))
        self.assertIn("nacimiento", validar_datos_paciente(nuevo(fecha_nacimiento="2031-01-01"), HOY))
        self.assertIn("nacimiento", validar_datos_paciente(nuevo(fecha_nacimiento="10/06/95"), HOY))


class PruebasCuentaPropia(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        self.bd = self.temp.bd

    def tearDown(self):
        self.temp.limpiar()

    def test_paciente_nuevo_crea_cuenta_e_inicia_sesion(self):
        resultado = crear_cuenta_paciente(self.bd, nuevo(), HOY)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIn("Bienvenido(a), Sofía", resultado["mensaje"])
        paciente = self.bd.obtener_paciente(resultado["id_paciente"])
        self.assertEqual(paciente["telefono"], "4771234567")
        sesion = iniciar_sesion(self.bd, "sofia.lara", "Sonrisa2030")["sesion"]
        self.assertEqual(sesion["rol"], "paciente")
        self.assertEqual(sesion["id_paciente"], resultado["id_paciente"])

    def test_contrasena_debil_o_distinta(self):
        self.assertEqual(crear_cuenta_paciente(self.bd, nuevo(contrasena="corta1",
                                                              confirmacion="corta1"), HOY)["mensaje"],
                         MENSAJE_CONTRASENA_DEBIL)
        self.assertEqual(crear_cuenta_paciente(self.bd, nuevo(contrasena="solotexto",
                                                              confirmacion="solotexto"), HOY)["mensaje"],
                         MENSAJE_CONTRASENA_DEBIL)
        self.assertEqual(crear_cuenta_paciente(self.bd, nuevo(confirmacion="Otra2030"), HOY)["mensaje"],
                         MENSAJE_CONTRASENAS_DISTINTAS)

    def test_usuario_invalido(self):
        for usuario in ("abc", "con espacio", "ñandú!"):
            self.assertEqual(crear_cuenta_paciente(self.bd, nuevo(usuario=usuario), HOY)["mensaje"],
                             MENSAJE_USUARIO_INVALIDO)

    def test_telefono_duplicado_remite_a_recepcion(self):
        crear_cuenta_paciente(self.bd, nuevo(), HOY)
        resultado = crear_cuenta_paciente(self.bd, nuevo(usuario="otra.cuenta"), HOY)
        self.assertFalse(resultado["exito"])
        self.assertIn("recepción", resultado["mensaje"])

    def test_usuario_ocupado_no_deja_paciente_huerfano(self):
        crear_cuenta_paciente(self.bd, nuevo(), HOY)
        resultado = crear_cuenta_paciente(self.bd, nuevo(telefono="4779998877"), HOY)
        self.assertIn("ya está en uso", resultado["mensaje"])
        self.assertEqual(len(self.bd.listar_pacientes()), 1)

    def test_base_no_disponible(self):
        resultado = crear_cuenta_paciente(BaseDatos(ruta_no_disponible()), nuevo(), HOY)
        self.assertIn("base de datos", resultado["mensaje"])


class PruebasRecepcion(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        self.bd = self.temp.bd

    def tearDown(self):
        self.temp.limpiar()

    def test_registrar_paciente_sin_acceso(self):
        resultado = registrar_paciente(self.bd, RECEPCION,
                                       nuevo(usuario="", contrasena=""), HOY)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIsNone(self.bd.obtener_usuario_de_paciente(resultado["id_paciente"]))

    def test_registrar_paciente_con_acceso(self):
        resultado = registrar_paciente(self.bd, RECEPCION, nuevo(), HOY)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIn("sofia.lara", resultado["mensaje"])
        self.assertTrue(iniciar_sesion(self.bd, "sofia.lara", "Sonrisa2030")["exito"])

    def test_solo_recepcion_registra(self):
        for rol in ("paciente", "dentista"):
            resultado = registrar_paciente(self.bd, {"rol": rol}, nuevo(), HOY)
            self.assertIn("no tiene permiso", resultado["mensaje"])

    def test_crear_acceso_a_paciente_existente(self):
        id_paciente = registrar_paciente(self.bd, RECEPCION,
                                         nuevo(usuario="", contrasena=""), HOY)["id_paciente"]
        resultado = gestionar_acceso(self.bd, RECEPCION, id_paciente, "sofia.l", "Dientes2030")
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIn("Acceso creado", resultado["mensaje"])
        self.assertTrue(iniciar_sesion(self.bd, "sofia.l", "Dientes2030")["exito"])

    def test_restablecer_contrasena_olvidada(self):
        id_paciente = registrar_paciente(self.bd, RECEPCION, nuevo(), HOY)["id_paciente"]
        resultado = gestionar_acceso(self.bd, RECEPCION, id_paciente, "", "Nueva2030x")
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIn("restablecida", resultado["mensaje"])
        self.assertFalse(iniciar_sesion(self.bd, "sofia.lara", "Sonrisa2030")["exito"])
        self.assertTrue(iniciar_sesion(self.bd, "sofia.lara", "Nueva2030x")["exito"])

    def test_acceso_errores(self):
        self.assertIn("no existe", gestionar_acceso(self.bd, RECEPCION, 99, "x.y.z", "Abcdef12")["mensaje"])
        self.assertIn("no tiene permiso",
                      gestionar_acceso(self.bd, {"rol": "paciente"}, 1, "x", "y")["mensaje"])

    def test_listar_y_buscar_pacientes(self):
        registrar_paciente(self.bd, RECEPCION, nuevo(), HOY)
        registrar_paciente(self.bd, RECEPCION, nuevo(nombre="Hugo", apellidos="Mena",
                                                     telefono="4770001111", usuario="",
                                                     contrasena=""), HOY)
        todos = listar_pacientes(self.bd, RECEPCION)["pacientes"]
        self.assertEqual(len(todos), 2)
        self.assertEqual({p["nombre_usuario"] for p in todos}, {"sofia.lara", None})
        self.assertEqual(len(listar_pacientes(self.bd, RECEPCION, "mena")["pacientes"]), 1)
        self.assertEqual(len(listar_pacientes(self.bd, RECEPCION, "477000")["pacientes"]), 1)
        self.assertFalse(listar_pacientes(self.bd, {"rol": "paciente"})["exito"])


if __name__ == "__main__":
    unittest.main()

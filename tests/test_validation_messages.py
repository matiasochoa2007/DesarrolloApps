"""Pruebas de M6 Validación y mensajes.

Ejecutar desde la carpeta orthoimagen_dental/:
    python -m unittest tests.test_validation_messages -v
"""

import unittest

from modules.validation_messages import (
    MENSAJE_HORARIO_OCUPADO,
    construir_mensaje_faltantes,
    esta_vacio,
    obtener_campos_faltantes,
    validar_cita,
)


def cita_completa(**cambios):
    """Datos de una cita válida; `cambios` sobrescribe campos."""
    datos = {
        "fecha": "2026-11-10",
        "hora": "10:00",
        "dentista": "Dra. Peña",
        "servicio": "Limpieza dental",
    }
    datos.update(cambios)
    return datos


class PruebasCriteriosDeAceptacion(unittest.TestCase):
    """Pruebas ligadas a CA-45, CA-46, CA-47 y CA-03."""

    def test_normal_ca45_un_solo_campo_faltante(self):
        resultado = validar_cita(cita_completa(servicio=""))
        self.assertFalse(resultado["valido"])
        self.assertEqual(resultado["campos_faltantes"], ["servicio"])
        self.assertEqual(
            resultado["mensaje"],
            "Error: El campo 'servicio' es obligatorio. Por favor, complételo.",
        )

    def test_limite_ca46_todos_los_campos_vacios(self):
        resultado = validar_cita(
            {"fecha": "", "hora": "", "dentista": "", "servicio": ""}
        )
        self.assertFalse(resultado["valido"])
        self.assertEqual(
            resultado["campos_faltantes"],
            ["fecha", "hora", "dentista", "servicio"],
        )
        self.assertEqual(
            resultado["mensaje"],
            "Error: Los siguientes campos son obligatorios y están vacíos: "
            "fecha, hora, dentista, servicio.",
        )

    def test_error_ca47_horario_ocupado(self):
        resultado = validar_cita(cita_completa(), horario_ocupado=True)
        self.assertFalse(resultado["valido"])
        self.assertEqual(resultado["campos_faltantes"], [])
        self.assertEqual(resultado["mensaje"], MENSAJE_HORARIO_OCUPADO)
        self.assertIn("no está disponible", resultado["mensaje"])
        self.assertIn("elija un horario diferente", resultado["mensaje"])

    def test_apoyo_ca03_paciente_deja_campo_vacio(self):
        resultado = validar_cita(cita_completa(dentista=None))
        self.assertFalse(resultado["valido"])
        self.assertEqual(resultado["campos_faltantes"], ["dentista"])
        self.assertIn("'dentista'", resultado["mensaje"])


class PruebasReglasAdicionales(unittest.TestCase):
    """Reglas de la orden de implementación corregida."""

    def test_datos_completos_son_validos(self):
        resultado = validar_cita(cita_completa())
        self.assertEqual(
            resultado, {"valido": True, "campos_faltantes": [], "mensaje": ""}
        )

    def test_paciente_no_requerido_no_se_exige(self):
        resultado = validar_cita(cita_completa(), requiere_paciente=False)
        self.assertTrue(resultado["valido"])

    def test_paciente_requerido_por_recepcionista(self):
        resultado = validar_cita(cita_completa(), requiere_paciente=True)
        self.assertFalse(resultado["valido"])
        self.assertEqual(resultado["campos_faltantes"], ["paciente"])

    def test_paciente_requerido_y_capturado_es_valido(self):
        resultado = validar_cita(
            cita_completa(paciente="Ana Peña Núñez"), requiere_paciente=True
        )
        self.assertTrue(resultado["valido"])

    def test_campo_con_solo_espacios_cuenta_como_vacio(self):
        resultado = validar_cita(cita_completa(hora="   "))
        self.assertEqual(resultado["campos_faltantes"], ["hora"])

    def test_campos_faltantes_tienen_prioridad_sobre_horario_ocupado(self):
        resultado = validar_cita(cita_completa(fecha=""), horario_ocupado=True)
        self.assertEqual(resultado["campos_faltantes"], ["fecha"])
        self.assertNotEqual(resultado["mensaje"], MENSAJE_HORARIO_OCUPADO)

    def test_campo_ausente_cuenta_como_faltante(self):
        datos = cita_completa()
        del datos["servicio"]
        self.assertEqual(obtener_campos_faltantes(datos), ["servicio"])

    def test_datos_none_se_trata_como_formulario_vacio(self):
        resultado = validar_cita(None)
        self.assertEqual(
            resultado["campos_faltantes"],
            ["fecha", "hora", "dentista", "servicio"],
        )

    def test_datos_de_tipo_invalido_lanza_typeerror(self):
        with self.assertRaises(TypeError):
            validar_cita("no soy un diccionario")

    def test_no_modifica_los_datos_recibidos(self):
        datos = cita_completa(hora="  ")
        copia = dict(datos)
        validar_cita(datos, horario_ocupado=True, requiere_paciente=True)
        self.assertEqual(datos, copia)

    def test_funciones_auxiliares(self):
        self.assertTrue(esta_vacio(None))
        self.assertTrue(esta_vacio(""))
        self.assertTrue(esta_vacio("  "))
        self.assertFalse(esta_vacio("10:00"))
        self.assertEqual(construir_mensaje_faltantes([]), "")


if __name__ == "__main__":
    unittest.main()

"""Pruebas de M2 Gestión de citas: registro (RF-01, RF-02).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_appointments -v
"""

import unittest
from datetime import date

from modules.appointments import (
    MENSAJE_PACIENTE_INEXISTENTE,
    MENSAJE_SERVICIO_INEXISTENTE,
    registrar_cita,
)
from modules.availability import MENSAJE_DENTISTA_INEXISTENTE
from modules.data_access import BaseDatos
from modules.validation_messages import MENSAJE_HORARIO_OCUPADO
from tests.utilidades import BaseTemporal, ruta_no_disponible

FECHA = "2030-03-04"
HOY = date(2030, 3, 1)


class EscenarioCitas(unittest.TestCase):
    """Base con dos pacientes, dos dentistas y un servicio."""

    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.bd = self.temp.bd
        self.p1 = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.p2 = bd.insertar_paciente("Luis", "Gómez", "4774445566")
        self.o1 = bd.insertar_odontologo("Laura", "Peña")
        self.o2 = bd.insertar_odontologo("Jorge", "Ruiz")
        self.s = bd.insertar_servicio("Limpieza dental", 45)
        self.s2 = bd.insertar_servicio("Valoración inicial", 30)
        self.paciente = {"rol": "paciente", "id_paciente": self.p1}
        self.paciente2 = {"rol": "paciente", "id_paciente": self.p2}
        self.recepcion = {"rol": "recepcionista"}
        self.dentista = {"rol": "dentista", "id_odontologo": self.o1}

    def tearDown(self):
        self.temp.limpiar()

    def datos(self, **cambios):
        datos = {"fecha": FECHA, "hora": "10:00", "dentista": self.o1,
                 "servicio": self.s, "motivo": "Revisión"}
        datos.update(cambios)
        return datos

    def registrar(self, sesion, **cambios):
        return registrar_cita(self.bd, sesion, self.datos(**cambios), hoy=HOY)


class PruebasRegistroPaciente(EscenarioCitas):
    """HU-01: el paciente registra su propia cita."""

    def test_ca01_paciente_registra_su_cita(self):
        resultado = self.registrar(self.paciente)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        cita = self.bd.obtener_cita(resultado["id_cita"])
        self.assertEqual(cita["id_paciente"], self.p1)
        self.assertEqual(cita["estatus"], "Programada")
        self.assertIn("Cita registrada", resultado["mensaje"])
        self.assertIn("Laura Peña", resultado["mensaje"])

    def test_ca01_paciente_no_puede_registrar_a_nombre_de_otro(self):
        resultado = self.registrar(self.paciente, paciente=self.p2)
        cita = self.bd.obtener_cita(resultado["id_cita"])
        self.assertEqual(cita["id_paciente"], self.p1)

    def test_ca02_ultimo_horario_del_dia_y_motivo_opcional(self):
        resultado = self.registrar(self.paciente, hora="17:00", motivo="  ")
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIsNone(self.bd.obtener_cita(resultado["id_cita"])["motivo"])

    def test_ca03_campo_vacio_nombra_el_campo(self):
        resultado = self.registrar(self.paciente, servicio="")
        self.assertFalse(resultado["exito"])
        self.assertEqual(
            resultado["mensaje"],
            "Error: El campo 'servicio' es obligatorio. Por favor, complételo.",
        )

    def test_ca03_todos_los_campos_vacios(self):
        resultado = registrar_cita(self.bd, self.paciente, {}, hoy=HOY)
        self.assertIn("fecha, hora, dentista, servicio", resultado["mensaje"])


class PruebasRegistroRecepcionista(EscenarioCitas):
    """HU-02: la recepcionista registra a nombre de un paciente."""

    def test_ca04_recepcionista_registra_para_un_paciente(self):
        resultado = self.registrar(self.recepcion, paciente=self.p2)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertEqual(self.bd.obtener_cita(resultado["id_cita"])["id_paciente"],
                         self.p2)

    def test_ca05_recepcionista_debe_indicar_el_paciente(self):
        resultado = self.registrar(self.recepcion)
        self.assertFalse(resultado["exito"])
        self.assertIn("'paciente'", resultado["mensaje"])

    def test_ca06_paciente_inexistente(self):
        for paciente in (999, "abc"):
            resultado = self.registrar(self.recepcion, paciente=paciente)
            self.assertFalse(resultado["exito"])
            self.assertEqual(resultado["mensaje"], MENSAJE_PACIENTE_INEXISTENTE)

    def test_dentista_no_registra_citas(self):
        resultado = self.registrar(self.dentista)
        self.assertFalse(resultado["exito"])
        self.assertIn("no tiene permiso", resultado["mensaje"])


class PruebasSinEmpalmesRF02(EscenarioCitas):
    """HU-03: un dentista no tiene dos citas a la misma hora."""

    def test_ca07_horarios_distintos_del_mismo_dentista(self):
        self.assertTrue(self.registrar(self.paciente, hora="10:00")["exito"])
        self.assertTrue(self.registrar(self.paciente2, hora="11:00")["exito"])

    def test_ca08_misma_hora_con_otro_dentista(self):
        self.assertTrue(self.registrar(self.paciente)["exito"])
        self.assertTrue(self.registrar(self.paciente2, dentista=self.o2)["exito"])

    def test_ca09_misma_hora_mismo_dentista_rechazada_con_ca47(self):
        self.assertTrue(self.registrar(self.paciente)["exito"])
        resultado = self.registrar(self.paciente2)
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_HORARIO_OCUPADO)
        self.assertIsNone(resultado["id_cita"])

    def test_campos_faltantes_tienen_prioridad_sobre_horario_ocupado(self):
        self.registrar(self.paciente)
        resultado = self.registrar(self.paciente2, servicio=None)
        self.assertIn("'servicio'", resultado["mensaje"])


class PruebasValidacionDeDatos(EscenarioCitas):
    def test_fecha_pasada_o_invalida(self):
        self.assertIn("ya pasó", self.registrar(self.paciente, fecha="2030-02-01")["mensaje"])
        self.assertIn("no es válida", self.registrar(self.paciente, fecha="4/3/30")["mensaje"])

    def test_hora_fuera_de_horario(self):
        self.assertIn("no es un horario", self.registrar(self.paciente, hora="20:00")["mensaje"])

    def test_dentista_o_servicio_inexistente(self):
        self.assertEqual(self.registrar(self.paciente, dentista=99)["mensaje"],
                         MENSAJE_DENTISTA_INEXISTENTE)
        self.assertEqual(self.registrar(self.paciente, servicio=99)["mensaje"],
                         MENSAJE_SERVICIO_INEXISTENTE)

    def test_ids_como_texto_desde_la_consola(self):
        resultado = self.registrar(self.recepcion, dentista=f" {self.o1} ",
                                   servicio=str(self.s), paciente=str(self.p1))
        self.assertTrue(resultado["exito"], resultado["mensaje"])

    def test_no_modifica_los_datos_recibidos(self):
        datos = self.datos(hora=" 10:00 ")
        copia = dict(datos)
        registrar_cita(self.bd, self.paciente, datos, hoy=HOY)
        self.assertEqual(datos, copia)

    def test_base_no_disponible(self):
        resultado = registrar_cita(BaseDatos(ruta_no_disponible()), self.paciente,
                                   self.datos(), hoy=HOY)
        self.assertFalse(resultado["exito"])
        self.assertIn("base de datos", resultado["mensaje"])


if __name__ == "__main__":
    unittest.main()

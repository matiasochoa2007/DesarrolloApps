"""Pruebas de M3 Disponibilidad (RF-07, RF-02).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_availability -v
"""

import unittest
from datetime import date

from modules.availability import (
    MENSAJE_DENTISTA_INEXISTENTE,
    consultar_disponibilidad,
    horario_ocupado,
    horarios_del_dia,
    validar_fecha,
    validar_hora,
)
from modules.data_access import BaseDatos
from tests.utilidades import BaseTemporal, ruta_no_disponible

FECHA = "2030-03-04"
HOY = date(2030, 3, 1)


class PruebasValidaciones(unittest.TestCase):
    def test_horarios_del_dia(self):
        horarios = horarios_del_dia()
        self.assertEqual(horarios[0], "09:00")
        self.assertEqual(horarios[-1], "17:00")
        self.assertEqual(len(horarios), 9)

    def test_validar_fecha(self):
        self.assertEqual(validar_fecha(FECHA, HOY), "")
        self.assertEqual(validar_fecha("2030-03-01", HOY), "")
        self.assertIn("ya pasó", validar_fecha("2030-02-28", HOY))
        self.assertIn("no es válida", validar_fecha("04/03/2030", HOY))
        self.assertIn("no es válida", validar_fecha("2030-02-30", HOY))
        self.assertIn("no es válida", validar_fecha("", HOY))

    def test_validar_hora(self):
        self.assertEqual(validar_hora("09:00"), "")
        self.assertIn("no es un horario de atención", validar_hora("08:00"))
        self.assertIn("no es un horario de atención", validar_hora("10:30"))
        self.assertIn("no es un horario de atención", validar_hora("18:00"))


class PruebasDisponibilidad(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.temp.bd
        self.p = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.o1 = bd.insertar_odontologo("Laura", "Peña")
        self.o2 = bd.insertar_odontologo("Jorge", "Ruiz")
        self.inactivo = bd.insertar_odontologo("Sofía", "Lara", activo=False)
        self.s = bd.insertar_servicio("Limpieza dental", 45)
        bd.insertar_cita(FECHA, "10:00", self.p, self.o1, self.s)
        self.paciente = {"rol": "paciente", "id_paciente": self.p}
        self.recepcion = {"rol": "recepcionista"}

    def tearDown(self):
        self.temp.limpiar()

    def consultar(self, sesion, odontologo=None, fecha=FECHA, bd=None):
        return consultar_disponibilidad(bd or self.temp.bd, sesion,
                                        odontologo or self.o1, fecha, hoy=HOY)

    # HU-12: el paciente consulta horarios libres
    def test_ca36_paciente_ve_horarios_libres(self):
        resultado = self.consultar(self.paciente)
        self.assertTrue(resultado["exito"])
        self.assertNotIn("10:00", resultado["libres"])
        self.assertIn("09:00", resultado["libres"])
        self.assertEqual(len(resultado["libres"]), 8)
        self.assertEqual(resultado["ocupados"], [])

    def test_ca37_dia_sin_horarios_libres(self):
        for hora in horarios_del_dia():
            if hora != "10:00":
                self.temp.bd.insertar_cita(FECHA, hora, self.p, self.o1, self.s)
        resultado = self.consultar(self.paciente)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["libres"], [])
        self.assertIn("no tiene horarios libres", resultado["mensaje"])

    def test_ca38_fecha_invalida_o_pasada(self):
        self.assertIn("no es válida", self.consultar(self.paciente, fecha="mañana")["mensaje"])
        self.assertIn("ya pasó", self.consultar(self.paciente, fecha="2020-01-01")["mensaje"])

    # HU-13: la recepcionista consulta disponibilidad
    def test_ca39_recepcionista_ve_libres_y_ocupados(self):
        resultado = self.consultar(self.recepcion)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["ocupados"], ["10:00"])
        self.assertEqual(len(resultado["libres"]), 8)

    def test_ca40_cita_cancelada_no_ocupa_el_horario(self):
        self.temp.bd.insertar_cita(FECHA, "12:00", self.p, self.o1, self.s,
                                   estatus="Cancelada")
        resultado = self.consultar(self.recepcion)
        self.assertIn("12:00", resultado["libres"])

    def test_ca41_dentista_inexistente_o_inactivo(self):
        for odontologo in (999, self.inactivo, "abc"):
            resultado = self.consultar(self.recepcion, odontologo=odontologo)
            self.assertFalse(resultado["exito"])
            self.assertEqual(resultado["mensaje"], MENSAJE_DENTISTA_INEXISTENTE)

    def test_cada_dentista_tiene_su_agenda(self):
        resultado = self.consultar(self.paciente, odontologo=self.o2)
        self.assertIn("10:00", resultado["libres"])

    def test_dentista_no_consulta_disponibilidad(self):
        resultado = self.consultar({"rol": "dentista", "id_odontologo": self.o1})
        self.assertFalse(resultado["exito"])
        self.assertIn("no tiene permiso", resultado["mensaje"])

    def test_base_no_disponible(self):
        resultado = self.consultar(self.recepcion, odontologo=1,
                                   bd=BaseDatos(ruta_no_disponible()))
        self.assertFalse(resultado["exito"])
        self.assertIn("base de datos", resultado["mensaje"])


class PruebasHorarioOcupadoRF02(unittest.TestCase):
    """HU-03: un dentista no tiene dos citas a la misma hora de inicio."""

    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.temp.bd
        self.p = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.o1 = bd.insertar_odontologo("Laura", "Peña")
        self.o2 = bd.insertar_odontologo("Jorge", "Ruiz")
        self.s = bd.insertar_servicio("Limpieza dental", 45)
        self.id_cita = bd.insertar_cita(FECHA, "10:00", self.p, self.o1, self.s)

    def tearDown(self):
        self.temp.limpiar()

    def test_ca07_horario_libre_no_esta_ocupado(self):
        self.assertFalse(horario_ocupado(self.temp.bd, self.o1, FECHA, "11:00"))

    def test_ca08_otro_dentista_misma_hora_no_esta_ocupado(self):
        self.assertFalse(horario_ocupado(self.temp.bd, self.o2, FECHA, "10:00"))

    def test_ca09_mismo_dentista_misma_hora_esta_ocupado(self):
        self.assertTrue(horario_ocupado(self.temp.bd, self.o1, FECHA, "10:00"))

    def test_la_cita_no_choca_consigo_misma(self):
        self.assertFalse(horario_ocupado(self.temp.bd, self.o1, FECHA, "10:00",
                                         excluir_id_cita=self.id_cita))


if __name__ == "__main__":
    unittest.main()

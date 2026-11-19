"""Pruebas de M4 Consulta de agenda (RF-06).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_agenda -v
"""

import unittest
from datetime import date

from modules.agenda import (
    MENSAJE_PACIENTE_INEXISTENTE,
    MENSAJE_SIN_CITAS_PACIENTE,
    MENSAJE_SIN_RESULTADOS,
    MENSAJE_SOLO_AGENDA_PROPIA,
    MENSAJE_SOLO_PROPIAS,
    agenda_dentista,
    filtrar_citas,
    formatear_cita,
    mis_citas,
)
from modules.appointments import registrar_cita
from modules.availability import MENSAJE_DENTISTA_INEXISTENTE
from modules.data_access import BaseDatos
from tests.utilidades import BaseTemporal, ruta_no_disponible

DIA1 = "2030-03-04"
DIA2 = "2030-03-05"
HOY = date(2030, 3, 1)


class EscenarioAgenda(unittest.TestCase):
    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.bd = self.temp.bd
        self.p1 = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.p2 = bd.insertar_paciente("Luis", "Gómez", "4774445566")
        self.p3 = bd.insertar_paciente("Eva", "Soto", "4777778899")
        self.o1 = bd.insertar_odontologo("Laura", "Peña")
        self.o2 = bd.insertar_odontologo("Jorge", "Ruiz")
        self.s = bd.insertar_servicio("Limpieza dental", 45)
        self.paciente1 = {"rol": "paciente", "id_paciente": self.p1}
        self.paciente3 = {"rol": "paciente", "id_paciente": self.p3}
        self.recepcion = {"rol": "recepcionista"}
        self.dentista1 = {"rol": "dentista", "id_odontologo": self.o1}
        self.dentista2 = {"rol": "dentista", "id_odontologo": self.o2}
        # Ana: dos citas con Laura; Luis: una con Jorge y una cancelada con Laura.
        bd.insertar_cita(DIA1, "10:00", self.p1, self.o1, self.s)
        bd.insertar_cita(DIA2, "09:00", self.p1, self.o1, self.s)
        bd.insertar_cita(DIA1, "11:00", self.p2, self.o2, self.s)
        bd.insertar_cita(DIA1, "12:00", self.p2, self.o1, self.s, estatus="Cancelada")

    def tearDown(self):
        self.temp.limpiar()


class PruebasPacienteHU09(EscenarioAgenda):
    def test_ca27_paciente_ve_sus_citas(self):
        resultado = mis_citas(self.bd, self.paciente1)
        self.assertTrue(resultado["exito"])
        self.assertEqual(len(resultado["citas"]), 2)
        self.assertTrue(all(c["id_paciente"] == self.p1 for c in resultado["citas"]))
        self.assertEqual([c["fecha"] for c in resultado["citas"]], [DIA1, DIA2])

    def test_ca01_cita_registrada_aparece_en_mis_citas(self):
        registro = registrar_cita(self.bd, self.paciente3,
                                  {"fecha": DIA2, "hora": "13:00", "dentista": self.o2,
                                   "servicio": self.s}, hoy=HOY)
        citas = mis_citas(self.bd, self.paciente3)["citas"]
        self.assertEqual([c["id_cita"] for c in citas], [registro["id_cita"]])

    def test_ca28_paciente_sin_citas(self):
        resultado = mis_citas(self.bd, self.paciente3)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["citas"], [])
        self.assertEqual(resultado["mensaje"], MENSAJE_SIN_CITAS_PACIENTE)

    def test_ca29_paciente_no_ve_citas_de_otro(self):
        resultado = mis_citas(self.bd, self.paciente1, id_paciente=self.p2)
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_SOLO_PROPIAS)
        self.assertFalse(filtrar_citas(self.bd, self.paciente1, id_paciente=self.p2)["exito"])


class PruebasRecepcionHU10(EscenarioAgenda):
    def test_ca30_filtrar_por_dia(self):
        resultado = filtrar_citas(self.bd, self.recepcion, fecha=DIA1)
        self.assertTrue(resultado["exito"])
        self.assertEqual([c["hora"] for c in resultado["citas"]],
                         ["10:00", "11:00", "12:00"])

    def test_ca30_filtrar_por_dentista_y_por_paciente(self):
        por_dentista = filtrar_citas(self.bd, self.recepcion, id_odontologo=self.o2)
        self.assertEqual(len(por_dentista["citas"]), 1)
        por_paciente = filtrar_citas(self.bd, self.recepcion, id_paciente=str(self.p1))
        self.assertEqual(len(por_paciente["citas"]), 2)
        combinado = filtrar_citas(self.bd, self.recepcion, fecha=DIA1,
                                  id_odontologo=self.o1, id_paciente=self.p1)
        self.assertEqual(len(combinado["citas"]), 1)

    def test_ca30_sin_filtros_muestra_todas(self):
        self.assertEqual(len(filtrar_citas(self.bd, self.recepcion, "", "", "")["citas"]), 4)

    def test_ca31_filtro_sin_resultados(self):
        resultado = filtrar_citas(self.bd, self.recepcion, fecha="2030-12-25")
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["citas"], [])
        self.assertEqual(resultado["mensaje"], MENSAJE_SIN_RESULTADOS)

    def test_ca32_fecha_invalida(self):
        resultado = filtrar_citas(self.bd, self.recepcion, fecha="31-12-2030")
        self.assertFalse(resultado["exito"])
        self.assertIn("no es válida", resultado["mensaje"])

    def test_ca32_paciente_o_dentista_inexistente(self):
        self.assertEqual(filtrar_citas(self.bd, self.recepcion, id_paciente=99)["mensaje"],
                         MENSAJE_PACIENTE_INEXISTENTE)
        self.assertEqual(filtrar_citas(self.bd, self.recepcion, id_odontologo="x")["mensaje"],
                         MENSAJE_DENTISTA_INEXISTENTE)

    def test_fechas_pasadas_permitidas_para_historial(self):
        self.assertTrue(filtrar_citas(self.bd, self.recepcion, fecha="2020-01-01")["exito"])


class PruebasDentistaHU11(EscenarioAgenda):
    def test_ca33_dentista_ve_su_agenda_del_dia(self):
        resultado = agenda_dentista(self.bd, self.dentista1, DIA1)
        self.assertTrue(resultado["exito"])
        # La cita cancelada de las 12:00 no aparece en la agenda.
        self.assertEqual([c["hora"] for c in resultado["citas"]], ["10:00"])

    def test_ca34_dia_sin_citas(self):
        resultado = agenda_dentista(self.bd, self.dentista2, DIA2)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["citas"], [])
        self.assertIn("No tiene citas programadas", resultado["mensaje"])

    def test_ca35_dentista_no_ve_agenda_de_otro(self):
        resultado = agenda_dentista(self.bd, self.dentista1, DIA1, id_odontologo=self.o2)
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_SOLO_AGENDA_PROPIA)

    def test_fecha_invalida_en_agenda(self):
        self.assertFalse(agenda_dentista(self.bd, self.dentista1, "hoy")["exito"])


class PruebasGenerales(EscenarioAgenda):
    def test_roles_no_autorizados(self):
        self.assertFalse(mis_citas(self.bd, self.recepcion)["exito"])
        self.assertFalse(filtrar_citas(self.bd, self.dentista1)["exito"])
        self.assertFalse(agenda_dentista(self.bd, self.paciente1, DIA1)["exito"])

    def test_base_no_disponible(self):
        bd = BaseDatos(ruta_no_disponible())
        self.assertIn("base de datos", mis_citas(bd, self.paciente1)["mensaje"])
        self.assertIn("base de datos", filtrar_citas(bd, self.recepcion)["mensaje"])
        self.assertIn("base de datos", agenda_dentista(bd, self.dentista1, DIA1)["mensaje"])

    def test_formatear_cita(self):
        cita = mis_citas(self.bd, self.paciente1)["citas"][0]
        texto = formatear_cita(cita)
        self.assertIn(f"{DIA1} 10:00", texto)
        self.assertIn("Ana Pérez con Laura Peña", texto)
        self.assertIn("Programada", texto)


if __name__ == "__main__":
    unittest.main()

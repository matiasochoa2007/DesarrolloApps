"""Pruebas de M2 Gestión de citas: modificar, cancelar y eliminar.

RF-03 (HU-04, HU-05), RF-04 (HU-06, HU-07) y RF-05 (HU-08).

Ejecutar desde la raíz del repositorio:
    py -m unittest tests.test_appointments_cambios -v
"""

import unittest
from datetime import date

from modules.appointments import (
    MENSAJE_CAMBIO_DENTISTA_RECEPCION,
    MENSAJE_CITA_AJENA,
    cancelar_cita,
    modificar_cita,
    registrar_cita,
)
from modules.availability import consultar_disponibilidad
from modules.data_access import BaseDatos
from modules.validation_messages import MENSAJE_HORARIO_OCUPADO
from tests.utilidades import BaseTemporal, ruta_no_disponible

FECHA = "2030-03-04"
OTRA_FECHA = "2030-03-06"
HOY = date(2030, 3, 1)


class EscenarioCambios(unittest.TestCase):
    """Ana tiene una cita a las 10:00 y Luis a las 11:00, ambas con Laura."""

    def setUp(self):
        self.temp = BaseTemporal()
        bd = self.bd = self.temp.bd
        self.p1 = bd.insertar_paciente("Ana", "Pérez", "4771112233")
        self.p2 = bd.insertar_paciente("Luis", "Gómez", "4774445566")
        self.o1 = bd.insertar_odontologo("Laura", "Peña")
        self.o2 = bd.insertar_odontologo("Jorge", "Ruiz")
        self.s1 = bd.insertar_servicio("Limpieza dental", 45)
        self.s2 = bd.insertar_servicio("Valoración inicial", 30)
        self.paciente1 = {"rol": "paciente", "id_paciente": self.p1}
        self.paciente2 = {"rol": "paciente", "id_paciente": self.p2}
        self.recepcion = {"rol": "recepcionista"}
        self.dentista = {"rol": "dentista", "id_odontologo": self.o1}
        self.cita1 = self.registrar(self.paciente1, "10:00")
        self.cita2 = self.registrar(self.paciente2, "11:00")

    def tearDown(self):
        self.temp.limpiar()

    def registrar(self, sesion, hora, dentista=None):
        resultado = registrar_cita(self.bd, sesion, {
            "fecha": FECHA, "hora": hora, "dentista": dentista or self.o1,
            "servicio": self.s1}, hoy=HOY)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        return resultado["id_cita"]

    def modificar(self, sesion, id_cita, **cambios):
        return modificar_cita(self.bd, sesion, id_cita, cambios, hoy=HOY)

    def libres(self, dentista=None, fecha=FECHA):
        return consultar_disponibilidad(self.bd, self.recepcion, dentista or self.o1,
                                        fecha, hoy=HOY)["libres"]


class PruebasModificarPacienteHU04(EscenarioCambios):
    def test_ca10_cambiar_fecha_y_hora_libera_el_horario_anterior(self):
        resultado = self.modificar(self.paciente1, self.cita1,
                                   fecha=OTRA_FECHA, hora="12:00")
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        cita = self.bd.obtener_cita(self.cita1)
        self.assertEqual((cita["fecha"], cita["hora"]), (OTRA_FECHA, "12:00"))
        self.assertEqual(cita["estatus"], "Reprogramada")
        self.assertIn("10:00", self.libres())
        self.assertNotIn("12:00", self.libres(fecha=OTRA_FECHA))

    def test_ca11_cambiar_solo_el_servicio_no_choca_consigo_misma(self):
        resultado = self.modificar(self.paciente1, self.cita1, servicio=self.s2)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        cita = self.bd.obtener_cita(self.cita1)
        self.assertEqual(cita["servicio"], "Valoración inicial")
        self.assertEqual(cita["estatus"], "Programada")

    def test_ca12_mover_a_horario_ocupado_muestra_ca47(self):
        resultado = self.modificar(self.paciente1, self.cita1, hora="11:00")
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_HORARIO_OCUPADO)
        self.assertEqual(self.bd.obtener_cita(self.cita1)["hora"], "10:00")

    def test_ca13_paciente_no_modifica_cita_ajena(self):
        resultado = self.modificar(self.paciente1, self.cita2, hora="15:00")
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_CITA_AJENA)
        self.assertEqual(self.bd.obtener_cita(self.cita2)["hora"], "11:00")

    def test_paciente_no_cambia_de_dentista(self):
        resultado = self.modificar(self.paciente1, self.cita1, dentista=self.o2)
        self.assertEqual(resultado["mensaje"], MENSAJE_CAMBIO_DENTISTA_RECEPCION)


class PruebasModificarRecepcionHU05(EscenarioCambios):
    def test_ca14_recepcionista_cambia_el_dentista(self):
        resultado = self.modificar(self.recepcion, self.cita2, dentista=self.o2)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        cita = self.bd.obtener_cita(self.cita2)
        self.assertEqual(cita["dentista"], "Jorge Ruiz")
        self.assertEqual(cita["estatus"], "Reprogramada")
        self.assertIn("11:00", self.libres(self.o1))

    def test_ca15_mover_a_horario_liberado_por_un_cambio(self):
        self.modificar(self.recepcion, self.cita2, hora="14:00")
        resultado = self.modificar(self.recepcion, self.cita1, hora="11:00")
        self.assertTrue(resultado["exito"], resultado["mensaje"])

    def test_ca16_modificar_con_campo_vacio(self):
        resultado = self.modificar(self.recepcion, self.cita1, hora="  ")
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"],
                         "Error: El campo 'hora' es obligatorio. Por favor, complételo.")

    def test_modificar_con_datos_invalidos(self):
        self.assertIn("ya pasó",
                      self.modificar(self.recepcion, self.cita1, fecha="2030-01-01")["mensaje"])
        self.assertIn("no es un horario",
                      self.modificar(self.recepcion, self.cita1, hora="07:00")["mensaje"])

    def test_modificar_cita_inexistente(self):
        resultado = self.modificar(self.recepcion, 999, hora="12:00")
        self.assertFalse(resultado["exito"])
        self.assertIn("no existe", resultado["mensaje"])

    def test_dentista_no_modifica_citas(self):
        resultado = self.modificar(self.dentista, self.cita1, hora="12:00")
        self.assertIn("no tiene permiso", resultado["mensaje"])

    def test_base_no_disponible(self):
        resultado = modificar_cita(BaseDatos(ruta_no_disponible()), self.recepcion,
                                   self.cita1, {"hora": "12:00"}, hoy=HOY)
        self.assertIn("base de datos", resultado["mensaje"])


class PruebasCancelarPacienteHU06(EscenarioCambios):
    def test_ca17_cancelar_cambia_estatus_y_libera_horario(self):
        resultado = cancelar_cita(self.bd, self.paciente1, self.cita1)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertIn("cancelada", resultado["mensaje"])
        cita = self.bd.obtener_cita(self.cita1)
        self.assertEqual(cita["estatus"], "Cancelada")  # se conserva en historial
        self.assertIn("10:00", self.libres())

    def test_ca18_cancelar_la_unica_cita(self):
        unica = self.registrar({"rol": "paciente",
                                "id_paciente": self.bd.insertar_paciente("Eva", "Soto", "1")},
                               "15:00", dentista=self.o2)
        resultado = cancelar_cita(self.bd, self.recepcion, unica)
        self.assertTrue(resultado["exito"])
        self.assertEqual(self.libres(self.o2), self.libres(self.o2, OTRA_FECHA))

    def test_ca19_cancelar_una_cita_ya_cancelada(self):
        cancelar_cita(self.bd, self.paciente1, self.cita1)
        resultado = cancelar_cita(self.bd, self.paciente1, self.cita1)
        self.assertFalse(resultado["exito"])
        self.assertIn("ya está cancelada", resultado["mensaje"])

    def test_ca20_paciente_no_cancela_cita_ajena(self):
        resultado = cancelar_cita(self.bd, self.paciente1, self.cita2)
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["mensaje"], MENSAJE_CITA_AJENA)
        self.assertEqual(self.bd.obtener_cita(self.cita2)["estatus"], "Programada")


class PruebasCancelarRecepcionHU07(EscenarioCambios):
    def test_ca21_recepcionista_cancela_cualquier_cita(self):
        resultado = cancelar_cita(self.bd, self.recepcion, self.cita2)
        self.assertTrue(resultado["exito"], resultado["mensaje"])
        self.assertEqual(self.bd.obtener_cita(self.cita2)["estatus"], "Cancelada")

    def test_ca22_y_ca40_reservar_el_horario_recien_cancelado(self):
        cancelar_cita(self.bd, self.recepcion, self.cita1)
        self.assertIn("10:00", self.libres())  # CA-40
        nueva = self.registrar(self.paciente2, "10:00")  # CA-22
        self.assertEqual(self.bd.obtener_cita(nueva)["estatus"], "Programada")

    def test_ca15_mover_a_horario_liberado_por_cancelacion(self):
        cancelar_cita(self.bd, self.recepcion, self.cita2)
        resultado = self.modificar(self.paciente1, self.cita1, hora="11:00")
        self.assertTrue(resultado["exito"], resultado["mensaje"])

    def test_ca23_cancelar_cita_inexistente(self):
        resultado = cancelar_cita(self.bd, self.recepcion, 999)
        self.assertFalse(resultado["exito"])
        self.assertIn("no existe", resultado["mensaje"])

    def test_cita_cancelada_no_se_puede_modificar(self):
        cancelar_cita(self.bd, self.recepcion, self.cita1)
        resultado = self.modificar(self.recepcion, self.cita1, hora="15:00")
        self.assertFalse(resultado["exito"])
        self.assertIn("Cancelada", resultado["mensaje"])

    def test_dentista_no_cancela(self):
        self.assertIn("no tiene permiso",
                      cancelar_cita(self.bd, self.dentista, self.cita1)["mensaje"])


if __name__ == "__main__":
    unittest.main()

"""Utilidades compartidas por las pruebas.

Cada prueba trabaja con una base SQLite temporal que se borra al terminar,
para no tocar la base real del proyecto.
"""

import os
import shutil
import tempfile

from modules.data_access import BaseDatos


class BaseTemporal:
    """Crea una carpeta temporal con una base inicializada."""

    def __init__(self):
        self.carpeta = tempfile.mkdtemp(prefix="orthoimagen_")
        self.ruta = os.path.join(self.carpeta, "prueba.db")
        self.bd = BaseDatos(self.ruta)
        self.bd.inicializar()

    def reabrir(self):
        """Cierra la conexión y abre una nueva sobre el mismo archivo."""
        self.bd.cerrar()
        self.bd = BaseDatos(self.ruta)
        return self.bd

    def limpiar(self):
        self.bd.cerrar()
        shutil.rmtree(self.carpeta, ignore_errors=True)


def ruta_no_disponible():
    """Ruta dentro de una carpeta que no existe: SQLite no puede abrirla."""
    return os.path.join(tempfile.gettempdir(), "no_existe_orthoimagen", "x", "bd.db")

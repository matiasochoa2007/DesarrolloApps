"""M7 Acceso a datos - Orthoimagen Dental.

Único módulo con acceso directo a la base SQLite. Los demás módulos le piden
los datos a través de la clase BaseDatos y nunca escriben SQL.

Requerimiento: RF-09. Historia: HU-17. Criterios: CA-51, CA-52, CA-53.

Tablas (diseño mínimo de la práctica de persistencia):
    paciente, odontologo, servicio, usuario y cita.
"""

import sqlite3

from config import settings

MENSAJE_BASE_NO_DISPONIBLE = (
    "Error: No se pudo acceder a la base de datos. "
    "Intente de nuevo más tarde o avise a la recepción."
)

TABLAS = ("paciente", "odontologo", "servicio", "usuario", "cita")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS paciente (
    id_paciente      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           TEXT NOT NULL,
    apellidos        TEXT NOT NULL,
    telefono         TEXT NOT NULL,
    correo           TEXT,
    fecha_nacimiento TEXT
);

CREATE TABLE IF NOT EXISTS odontologo (
    id_odontologo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    apellidos     TEXT NOT NULL,
    especialidad  TEXT,
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS servicio (
    id_servicio  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    descripcion  TEXT,
    duracion_min INTEGER NOT NULL CHECK (duracion_min > 0),
    precio       REAL CHECK (precio IS NULL OR precio >= 0)
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario  TEXT NOT NULL UNIQUE,
    contrasena_hash TEXT NOT NULL,
    rol             TEXT NOT NULL
                    CHECK (rol IN ('paciente', 'recepcionista', 'dentista')),
    id_paciente     INTEGER REFERENCES paciente (id_paciente),
    id_odontologo   INTEGER REFERENCES odontologo (id_odontologo)
);

CREATE TABLE IF NOT EXISTS cita (
    id_cita       INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha         TEXT NOT NULL,
    hora          TEXT NOT NULL,
    motivo        TEXT,
    estatus       TEXT NOT NULL DEFAULT 'Programada'
                  CHECK (estatus IN
                         ('Programada', 'Reprogramada', 'Cancelada', 'Atendida')),
    id_paciente   INTEGER NOT NULL REFERENCES paciente (id_paciente),
    id_odontologo INTEGER NOT NULL REFERENCES odontologo (id_odontologo),
    id_servicio   INTEGER NOT NULL REFERENCES servicio (id_servicio)
);
"""


class ErrorBaseDatos(Exception):
    """La base no está disponible o falló una operación (CA-53)."""

    def __init__(self, detalle=""):
        super().__init__(MENSAJE_BASE_NO_DISPONIBLE)
        self.mensaje = MENSAJE_BASE_NO_DISPONIBLE
        self.detalle = detalle


class ErrorIntegridad(ErrorBaseDatos):
    """Se violó una regla de la base (dato duplicado o referencia inválida)."""


class BaseDatos:
    """Conexión a la base SQLite del proyecto.

    Uso:
        bd = BaseDatos("data/orthoimagen.db")
        bd.inicializar()
        ...
        bd.cerrar()
    """

    def __init__(self, ruta=None):
        self.ruta = str(ruta if ruta is not None else settings.RUTA_BD)
        self._conexion = None

    # -- Conexión -----------------------------------------------------------

    def conectar(self):
        """Abre la conexión si no está abierta. Lanza ErrorBaseDatos si falla."""
        if self._conexion is None:
            try:
                conexion = sqlite3.connect(self.ruta)
                conexion.row_factory = sqlite3.Row
                conexion.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as error:
                raise ErrorBaseDatos(str(error)) from error
            self._conexion = conexion
        return self._conexion

    def cerrar(self):
        """Cierra la conexión. Los datos ya guardados permanecen en el archivo."""
        if self._conexion is not None:
            self._conexion.close()
            self._conexion = None

    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, *_):
        self.cerrar()

    def inicializar(self):
        """Crea las tablas si no existen (no borra datos existentes)."""
        try:
            self.conectar().executescript(ESQUEMA)
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error

    def tablas(self):
        """Devuelve los nombres de las tablas del proyecto que existen."""
        filas = self._consultar(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [fila["name"] for fila in filas]

    # -- Ejecución interna ----------------------------------------------------

    def _ejecutar(self, sql, parametros=()):
        """Ejecuta una escritura, confirma y devuelve el cursor."""
        conexion = self.conectar()
        try:
            with conexion:
                return conexion.execute(sql, parametros)
        except sqlite3.IntegrityError as error:
            raise ErrorIntegridad(str(error)) from error
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error

    def _consultar(self, sql, parametros=()):
        """Ejecuta una lectura y devuelve una lista de diccionarios."""
        conexion = self.conectar()
        try:
            filas = conexion.execute(sql, parametros).fetchall()
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error
        return [dict(fila) for fila in filas]

    def _consultar_uno(self, sql, parametros=()):
        filas = self._consultar(sql, parametros)
        return filas[0] if filas else None

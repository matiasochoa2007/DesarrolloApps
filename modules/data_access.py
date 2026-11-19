"""M7 Acceso a datos - Orthoimagen Dental.

Único módulo con acceso directo a la base SQLite. Los demás módulos le piden
los datos a través de la clase BaseDatos y nunca escriben SQL.

Requerimiento: RF-09. Historia: HU-17. Criterios: CA-51, CA-52, CA-53.

Tablas (diseño mínimo de la práctica de persistencia):
    paciente, odontologo, servicio, usuario y cita.
"""

import sqlite3
import threading

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

-- RF-02: un dentista no puede tener dos citas activas a la misma hora de
-- inicio. Las citas canceladas no ocupan el horario.
CREATE UNIQUE INDEX IF NOT EXISTS ux_cita_odontologo_horario
    ON cita (id_odontologo, fecha, hora)
    WHERE estatus <> 'Cancelada';
"""

ESTATUS_PROGRAMADA = "Programada"
ESTATUS_REPROGRAMADA = "Reprogramada"
ESTATUS_CANCELADA = "Cancelada"
ESTATUS_ATENDIDA = "Atendida"


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
        self.candado = threading.RLock()

    # -- Conexión -----------------------------------------------------------

    def conectar(self):
        """Abre la conexión si no está abierta. Lanza ErrorBaseDatos si falla."""
        if self._conexion is None:
            try:
                # check_same_thread=False: la interfaz gráfica atiende cada
                # llamada en su propio hilo; el candado serializa el acceso.
                conexion = sqlite3.connect(self.ruta, check_same_thread=False)
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
            with self.candado, conexion:
                return conexion.execute(sql, parametros)
        except sqlite3.IntegrityError as error:
            raise ErrorIntegridad(str(error)) from error
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error

    def _consultar(self, sql, parametros=()):
        """Ejecuta una lectura y devuelve una lista de diccionarios."""
        conexion = self.conectar()
        try:
            with self.candado:
                filas = conexion.execute(sql, parametros).fetchall()
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error
        return [dict(fila) for fila in filas]

    def _consultar_uno(self, sql, parametros=()):
        filas = self._consultar(sql, parametros)
        return filas[0] if filas else None

    # -- Pacientes ------------------------------------------------------------

    def insertar_paciente(self, nombre, apellidos, telefono, correo=None,
                          fecha_nacimiento=None):
        cursor = self._ejecutar(
            "INSERT INTO paciente (nombre, apellidos, telefono, correo, "
            "fecha_nacimiento) VALUES (?, ?, ?, ?, ?)",
            (nombre, apellidos, telefono, correo, fecha_nacimiento),
        )
        return cursor.lastrowid

    def obtener_paciente(self, id_paciente):
        return self._consultar_uno(
            "SELECT * FROM paciente WHERE id_paciente = ?", (id_paciente,)
        )

    def listar_pacientes(self):
        return self._consultar(
            "SELECT * FROM paciente ORDER BY apellidos, nombre"
        )

    def buscar_paciente_por_telefono(self, telefono):
        return self._consultar_uno(
            "SELECT * FROM paciente WHERE telefono = ?", (telefono,)
        )

    def listar_pacientes_con_acceso(self):
        """Pacientes con el nombre de usuario de su acceso, si lo tienen."""
        return self._consultar(
            "SELECT p.*, u.id_usuario, u.nombre_usuario FROM paciente p "
            "LEFT JOIN usuario u ON u.id_paciente = p.id_paciente "
            "ORDER BY p.apellidos, p.nombre"
        )

    def insertar_paciente_con_usuario(self, nombre, apellidos, telefono,
                                      correo, fecha_nacimiento,
                                      nombre_usuario, contrasena_hash):
        """Guarda el paciente y su usuario en una sola transacción: si el
        usuario falla (p. ej. duplicado), tampoco queda el paciente."""
        conexion = self.conectar()
        try:
            with self.candado, conexion:
                cursor = conexion.execute(
                    "INSERT INTO paciente (nombre, apellidos, telefono, correo, "
                    "fecha_nacimiento) VALUES (?, ?, ?, ?, ?)",
                    (nombre, apellidos, telefono, correo, fecha_nacimiento),
                )
                id_paciente = cursor.lastrowid
                conexion.execute(
                    "INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, "
                    "id_paciente) VALUES (?, ?, 'paciente', ?)",
                    (nombre_usuario, contrasena_hash, id_paciente),
                )
        except sqlite3.IntegrityError as error:
            raise ErrorIntegridad(str(error)) from error
        except sqlite3.Error as error:
            raise ErrorBaseDatos(str(error)) from error
        return id_paciente

    # -- Odontólogos ----------------------------------------------------------

    def insertar_odontologo(self, nombre, apellidos, especialidad=None,
                            activo=True):
        cursor = self._ejecutar(
            "INSERT INTO odontologo (nombre, apellidos, especialidad, activo) "
            "VALUES (?, ?, ?, ?)",
            (nombre, apellidos, especialidad, 1 if activo else 0),
        )
        return cursor.lastrowid

    def obtener_odontologo(self, id_odontologo):
        return self._consultar_uno(
            "SELECT * FROM odontologo WHERE id_odontologo = ?", (id_odontologo,)
        )

    def listar_odontologos(self, solo_activos=True):
        sql = "SELECT * FROM odontologo"
        if solo_activos:
            sql += " WHERE activo = 1"
        return self._consultar(sql + " ORDER BY apellidos, nombre")

    # -- Servicios (catálogo, RF-08) -----------------------------------------

    def insertar_servicio(self, nombre, duracion_min, descripcion=None,
                          precio=None):
        cursor = self._ejecutar(
            "INSERT INTO servicio (nombre, descripcion, duracion_min, precio) "
            "VALUES (?, ?, ?, ?)",
            (nombre, descripcion, duracion_min, precio),
        )
        return cursor.lastrowid

    def obtener_servicio(self, id_servicio):
        return self._consultar_uno(
            "SELECT * FROM servicio WHERE id_servicio = ?", (id_servicio,)
        )

    def listar_servicios(self):
        return self._consultar("SELECT * FROM servicio ORDER BY nombre")

    # -- Usuarios (RF-11) ------------------------------------------------------

    def insertar_usuario(self, nombre_usuario, contrasena_hash, rol,
                         id_paciente=None, id_odontologo=None):
        cursor = self._ejecutar(
            "INSERT INTO usuario (nombre_usuario, contrasena_hash, rol, "
            "id_paciente, id_odontologo) VALUES (?, ?, ?, ?, ?)",
            (nombre_usuario, contrasena_hash, rol, id_paciente, id_odontologo),
        )
        return cursor.lastrowid

    def obtener_usuario_por_nombre(self, nombre_usuario):
        return self._consultar_uno(
            "SELECT * FROM usuario WHERE nombre_usuario = ?", (nombre_usuario,)
        )

    def obtener_usuario_de_paciente(self, id_paciente):
        return self._consultar_uno(
            "SELECT * FROM usuario WHERE id_paciente = ?", (id_paciente,)
        )

    def actualizar_contrasena(self, id_usuario, contrasena_hash):
        cursor = self._ejecutar(
            "UPDATE usuario SET contrasena_hash = ? WHERE id_usuario = ?",
            (contrasena_hash, id_usuario),
        )
        return cursor.rowcount

    def contar_usuarios(self):
        return self._consultar_uno("SELECT COUNT(*) AS total FROM usuario")["total"]

    # -- Citas (RF-01, RF-02) --------------------------------------------------

    def insertar_cita(self, fecha, hora, id_paciente, id_odontologo,
                      id_servicio, motivo=None, estatus=ESTATUS_PROGRAMADA):
        """Guarda una cita. Lanza ErrorIntegridad si el dentista ya tiene una
        cita activa a esa hora (índice único de RF-02)."""
        cursor = self._ejecutar(
            "INSERT INTO cita (fecha, hora, motivo, estatus, id_paciente, "
            "id_odontologo, id_servicio) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fecha, hora, motivo, estatus, id_paciente, id_odontologo,
             id_servicio),
        )
        return cursor.lastrowid

    def obtener_cita(self, id_cita):
        """Devuelve la cita con los nombres de paciente, dentista y servicio."""
        return self._consultar_uno(
            _SELECT_CITA_DETALLE + " WHERE c.id_cita = ?", (id_cita,)
        )

    def horas_ocupadas(self, id_odontologo, fecha, excluir_id_cita=None):
        """Horas de inicio con cita activa (no cancelada) del dentista ese día.

        `excluir_id_cita` permite ignorar una cita, por ejemplo la que se está
        modificando, para que no choque consigo misma.
        """
        filas = self._consultar(
            "SELECT hora FROM cita WHERE id_odontologo = ? AND fecha = ? "
            "AND estatus <> ? AND id_cita IS NOT ? ORDER BY hora",
            (id_odontologo, fecha, ESTATUS_CANCELADA, excluir_id_cita),
        )
        return [fila["hora"] for fila in filas]

    def actualizar_cita(self, id_cita, fecha, hora, id_odontologo, id_servicio,
                        motivo, estatus):
        """Reemplaza los datos de una cita. Devuelve las filas afectadas."""
        cursor = self._ejecutar(
            "UPDATE cita SET fecha = ?, hora = ?, id_odontologo = ?, "
            "id_servicio = ?, motivo = ?, estatus = ? WHERE id_cita = ?",
            (fecha, hora, id_odontologo, id_servicio, motivo, estatus, id_cita),
        )
        return cursor.rowcount

    def actualizar_estatus(self, id_cita, estatus):
        """Cambia el estatus de una cita. Devuelve las filas afectadas."""
        cursor = self._ejecutar(
            "UPDATE cita SET estatus = ? WHERE id_cita = ?", (estatus, id_cita)
        )
        return cursor.rowcount

    def eliminar_cita(self, id_cita):
        """Borra el registro de la cita (RF-05). Devuelve las filas borradas."""
        cursor = self._ejecutar("DELETE FROM cita WHERE id_cita = ?", (id_cita,))
        return cursor.rowcount

    def consultar_citas(self, id_paciente=None, id_odontologo=None, fecha=None,
                        incluir_canceladas=True):
        """Citas con detalle, filtradas por paciente, dentista o día (RF-06).

        Los filtros en None no se aplican. Orden: fecha y hora.
        """
        condiciones, parametros = [], []
        for columna, valor in (("c.id_paciente", id_paciente),
                               ("c.id_odontologo", id_odontologo),
                               ("c.fecha", fecha)):
            if valor is not None:
                condiciones.append(f"{columna} = ?")
                parametros.append(valor)
        if not incluir_canceladas:
            condiciones.append("c.estatus <> ?")
            parametros.append(ESTATUS_CANCELADA)
        sql = _SELECT_CITA_DETALLE
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        return self._consultar(sql + " ORDER BY c.fecha, c.hora, c.id_cita",
                               parametros)


_SELECT_CITA_DETALLE = """
SELECT c.id_cita, c.fecha, c.hora, c.motivo, c.estatus,
       c.id_paciente, c.id_odontologo, c.id_servicio,
       p.nombre || ' ' || p.apellidos AS paciente,
       o.nombre || ' ' || o.apellidos AS dentista,
       s.nombre AS servicio
FROM cita c
JOIN paciente p   ON p.id_paciente = c.id_paciente
JOIN odontologo o ON o.id_odontologo = c.id_odontologo
JOIN servicio s   ON s.id_servicio = c.id_servicio
"""

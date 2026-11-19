"""M1 Autenticación y roles - Orthoimagen Dental.

Inicia sesión con contraseña protegida con hash y controla qué puede hacer
cada rol del sistema.

Requerimiento: RF-11. Historia: HU-16. Criterios: CA-48, CA-49, CA-50.

Roles (según las historias de usuario §6.1):
    paciente, recepcionista y dentista.

Las contraseñas nunca se guardan en texto plano: se usa PBKDF2-SHA256 con
sal aleatoria (biblioteca estándar `hashlib`).
"""

import hashlib
import hmac
import secrets

from config import settings
from modules.data_access import ErrorBaseDatos, ErrorIntegridad
from modules.validation_messages import esta_vacio

ROL_PACIENTE = "paciente"
ROL_RECEPCIONISTA = "recepcionista"
ROL_DENTISTA = "dentista"
ROLES = (ROL_PACIENTE, ROL_RECEPCIONISTA, ROL_DENTISTA)

# Acciones del sistema y roles autorizados (matriz HU ↔ rol).
PERMISOS = {
    "consultar_catalogo": {ROL_PACIENTE, ROL_RECEPCIONISTA, ROL_DENTISTA},  # HU-14
    "consultar_disponibilidad": {ROL_PACIENTE, ROL_RECEPCIONISTA},  # HU-12, HU-13
    "registrar_cita_propia": {ROL_PACIENTE},  # HU-01
    "registrar_cita_para_paciente": {ROL_RECEPCIONISTA},  # HU-02
    "ver_mis_citas": {ROL_PACIENTE},  # HU-09
    "filtrar_citas": {ROL_RECEPCIONISTA},  # HU-10
    "ver_agenda_dentista": {ROL_DENTISTA},  # HU-11
    "modificar_cita": {ROL_PACIENTE, ROL_RECEPCIONISTA},  # HU-04, HU-05
    "cancelar_cita": {ROL_PACIENTE, ROL_RECEPCIONISTA},  # HU-06, HU-07
    "eliminar_cita": {ROL_RECEPCIONISTA},  # HU-08
    # Extensión v1.1 (RF-12 propuesto): pacientes nuevos y accesos.
    "registrar_paciente": {ROL_RECEPCIONISTA},
    "gestionar_accesos": {ROL_RECEPCIONISTA},
}

MENSAJE_CREDENCIALES_VACIAS = (
    "Error: Ingrese su usuario y su contraseña para iniciar sesión."
)
MENSAJE_CREDENCIALES_INCORRECTAS = "Error: Usuario o contraseña incorrectos."
MENSAJE_SIN_PERMISO = (
    "Error: Su rol ({rol}) no tiene permiso para realizar esta acción."
)
MENSAJE_SIN_SESION = "Error: Debe iniciar sesión para realizar esta acción."
MENSAJE_USUARIO_DUPLICADO = "Error: El nombre de usuario '{usuario}' ya existe."
MENSAJE_ROL_INVALIDO = "Error: El rol '{rol}' no existe en el sistema."
MENSAJE_VINCULO_FALTANTE = (
    "Error: Un usuario con rol {rol} debe estar vinculado a su {entidad}."
)

_ALGORITMO = "pbkdf2_sha256"


# -- Contraseñas -------------------------------------------------------------

def generar_hash(contrasena, iteraciones=None, sal=None):
    """Devuelve 'pbkdf2_sha256$iteraciones$sal$hash' para guardar en la BD."""
    iteraciones = iteraciones or settings.ITERACIONES_HASH
    sal = sal or secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac(
        "sha256", contrasena.encode("utf-8"), sal.encode("utf-8"), iteraciones
    )
    return f"{_ALGORITMO}${iteraciones}${sal}${derivado.hex()}"


def verificar_contrasena(contrasena, hash_guardado):
    """Compara la contraseña con el hash guardado en tiempo constante."""
    try:
        algoritmo, iteraciones, sal, esperado = hash_guardado.split("$")
        iteraciones = int(iteraciones)
    except (AttributeError, ValueError):
        return False
    if algoritmo != _ALGORITMO:
        return False
    calculado = generar_hash(contrasena, iteraciones, sal).split("$")[3]
    return hmac.compare_digest(calculado, esperado)


# -- Usuarios y sesión -------------------------------------------------------

def _resultado(exito, mensaje="", **datos):
    return {"exito": exito, "mensaje": mensaje, **datos}


def registrar_usuario(bd, nombre_usuario, contrasena, rol, id_paciente=None,
                      id_odontologo=None):
    """Crea un usuario con su contraseña protegida con hash.

    Un paciente debe vincularse a su registro de paciente y un dentista a su
    registro de odontólogo, para que solo vean sus propias citas.
    """
    if esta_vacio(nombre_usuario) or esta_vacio(contrasena):
        return _resultado(False, MENSAJE_CREDENCIALES_VACIAS)
    if rol not in ROLES:
        return _resultado(False, MENSAJE_ROL_INVALIDO.format(rol=rol))
    if rol == ROL_PACIENTE and id_paciente is None:
        return _resultado(
            False, MENSAJE_VINCULO_FALTANTE.format(rol=rol, entidad="paciente")
        )
    if rol == ROL_DENTISTA and id_odontologo is None:
        return _resultado(
            False, MENSAJE_VINCULO_FALTANTE.format(rol=rol, entidad="odontólogo")
        )
    try:
        id_usuario = bd.insertar_usuario(
            nombre_usuario.strip(), generar_hash(contrasena), rol,
            id_paciente, id_odontologo,
        )
    except ErrorIntegridad:
        return _resultado(
            False, MENSAJE_USUARIO_DUPLICADO.format(usuario=nombre_usuario.strip())
        )
    except ErrorBaseDatos as error:
        return _resultado(False, error.mensaje)
    return _resultado(True, id_usuario=id_usuario)


def iniciar_sesion(bd, nombre_usuario, contrasena):
    """Valida las credenciales y devuelve la sesión con el rol (CA-48, CA-50).

    Devuelve {"exito", "mensaje", "sesion"}; `sesion` es None si falla.
    El mensaje de error no revela si falló el usuario o la contraseña.
    """
    if esta_vacio(nombre_usuario) or esta_vacio(contrasena):
        return _resultado(False, MENSAJE_CREDENCIALES_VACIAS, sesion=None)
    try:
        usuario = bd.obtener_usuario_por_nombre(nombre_usuario.strip())
    except ErrorBaseDatos as error:
        return _resultado(False, error.mensaje, sesion=None)
    if usuario is None or not verificar_contrasena(
        contrasena, usuario["contrasena_hash"]
    ):
        return _resultado(False, MENSAJE_CREDENCIALES_INCORRECTAS, sesion=None)

    sesion = {
        "id_usuario": usuario["id_usuario"],
        "nombre_usuario": usuario["nombre_usuario"],
        "rol": usuario["rol"],
        "id_paciente": usuario["id_paciente"],
        "id_odontologo": usuario["id_odontologo"],
    }
    return _resultado(True, sesion=sesion)


def verificar_permiso(sesion, accion):
    """Indica si la sesión puede realizar la acción (CA-49).

    Devuelve {"exito", "mensaje"}.
    """
    if not sesion:
        return _resultado(False, MENSAJE_SIN_SESION)
    rol = sesion.get("rol")
    if rol in PERMISOS.get(accion, set()):
        return _resultado(True)
    return _resultado(False, MENSAJE_SIN_PERMISO.format(rol=rol))

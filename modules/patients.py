"""M8 Registro de pacientes y accesos - Orthoimagen Dental.

Extensión de la versión 1.1 (RF-12 propuesto, pendiente de aprobación del
profesor). Resuelve qué pasa con un cliente nuevo:

- Paciente nuevo: crea su propia cuenta desde la pantalla de inicio
  (`crear_cuenta_paciente`) y queda con sesión de paciente.
- Paciente nuevo que llama o acude en persona: la recepcionista lo registra
  (`registrar_paciente`), con o sin acceso al sistema.
- Paciente que ya existe pero no tiene usuario, u olvidó su contraseña: la
  recepcionista le crea o restablece el acceso (`gestionar_acceso`).

Justificación: el RNF de usabilidad habla de "un paciente nuevo" que agenda
en 5 pasos, y HU-01/HU-02 suponen que el paciente ya existe en el sistema.
"""

import re
from datetime import date, datetime

from modules.auth_roles import (
    ROL_PACIENTE,
    generar_hash,
    verificar_permiso,
)
from modules.data_access import ErrorBaseDatos, ErrorIntegridad
from modules.validation_messages import construir_mensaje_faltantes, esta_vacio

CAMPOS_PACIENTE = ("nombre", "apellidos", "telefono")

MENSAJE_TELEFONO_INVALIDO = (
    "Error: El teléfono debe tener 10 dígitos, por ejemplo 4771234567."
)
MENSAJE_CORREO_INVALIDO = (
    "Error: El correo '{correo}' no es válido. Use el formato nombre@dominio.com."
)
MENSAJE_NACIMIENTO_INVALIDO = (
    "Error: La fecha de nacimiento debe tener el formato AAAA-MM-DD y no puede "
    "ser futura."
)
MENSAJE_TELEFONO_DUPLICADO = (
    "Error: Ya hay un paciente registrado con el teléfono {telefono}. Si ya es "
    "paciente de la clínica, pida en recepción su usuario y contraseña."
)
MENSAJE_USUARIO_INVALIDO = (
    "Error: El usuario debe tener de 4 a 30 caracteres: letras, números, "
    "punto, guion o guion bajo, sin espacios."
)
MENSAJE_CONTRASENA_DEBIL = (
    "Error: La contraseña debe tener al menos 8 caracteres, con letras y números."
)
MENSAJE_CONTRASENAS_DISTINTAS = "Error: Las contraseñas no coinciden."
MENSAJE_USUARIO_OCUPADO = (
    "Error: El usuario '{usuario}' ya está en uso. Elija otro."
)
MENSAJE_PACIENTE_INEXISTENTE = "Error: El paciente seleccionado no existe."
MENSAJE_CUENTA_CREADA = (
    "¡Bienvenido(a), {nombre}! Su cuenta quedó lista; ya puede agendar su cita."
)
MENSAJE_PACIENTE_REGISTRADO = "Paciente registrado: {nombre} {apellidos} (expediente {id})."
MENSAJE_ACCESO_CREADO = "Acceso creado para {paciente}: usuario '{usuario}'."
MENSAJE_ACCESO_RESTABLECIDO = (
    "Contraseña restablecida para {paciente} (usuario '{usuario}')."
)

_PATRON_USUARIO = re.compile(r"^[A-Za-z0-9._-]{4,30}$")
_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _resultado(exito, mensaje, **datos):
    return {"exito": exito, "mensaje": mensaje, **datos}


def normalizar_telefono(telefono):
    """Quita espacios, guiones y paréntesis: '477 123-4567' → '4771234567'."""
    return re.sub(r"[\s\-().]", "", str(telefono or ""))


def _texto(valor):
    return valor.strip() if isinstance(valor, str) else valor


def validar_datos_paciente(datos, hoy=None):
    """Devuelve "" si los datos del paciente son válidos o el mensaje de error.

    Obligatorios: nombre, apellidos y teléfono (mensaje de M6 si faltan).
    Opcionales: correo y fecha de nacimiento, validados si se capturan.
    """
    datos = datos or {}
    faltantes = [c for c in CAMPOS_PACIENTE if esta_vacio(datos.get(c))]
    if faltantes:
        return construir_mensaje_faltantes(faltantes)
    if not re.fullmatch(r"\d{10}", normalizar_telefono(datos["telefono"])):
        return MENSAJE_TELEFONO_INVALIDO
    correo = _texto(datos.get("correo"))
    if not esta_vacio(correo) and not _PATRON_CORREO.match(correo):
        return MENSAJE_CORREO_INVALIDO.format(correo=correo)
    nacimiento = _texto(datos.get("fecha_nacimiento"))
    if not esta_vacio(nacimiento):
        try:
            dia = datetime.strptime(nacimiento, "%Y-%m-%d").date()
        except ValueError:
            return MENSAJE_NACIMIENTO_INVALIDO
        if dia > (hoy or date.today()):
            return MENSAJE_NACIMIENTO_INVALIDO
    return ""


def validar_credenciales(usuario, contrasena, confirmacion=None):
    """Reglas del usuario y la contraseña de un paciente."""
    faltantes = [campo for campo, valor in (("usuario", usuario),
                                            ("contraseña", contrasena))
                 if esta_vacio(valor)]
    if faltantes:
        return construir_mensaje_faltantes(faltantes)
    if not _PATRON_USUARIO.match(usuario.strip()):
        return MENSAJE_USUARIO_INVALIDO
    if (len(contrasena) < 8 or not re.search(r"[A-Za-z]", contrasena)
            or not re.search(r"\d", contrasena)):
        return MENSAJE_CONTRASENA_DEBIL
    if confirmacion is not None and confirmacion != contrasena:
        return MENSAJE_CONTRASENAS_DISTINTAS
    return ""


def _datos_limpios(datos):
    return {
        "nombre": _texto(datos["nombre"]),
        "apellidos": _texto(datos["apellidos"]),
        "telefono": normalizar_telefono(datos["telefono"]),
        "correo": None if esta_vacio(datos.get("correo")) else _texto(datos["correo"]),
        "fecha_nacimiento": (None if esta_vacio(datos.get("fecha_nacimiento"))
                             else _texto(datos["fecha_nacimiento"])),
    }


def _revisar_duplicados(bd, telefono, usuario=None):
    """Mensaje si el teléfono o el usuario ya existen; "" si no."""
    if bd.buscar_paciente_por_telefono(telefono) is not None:
        return MENSAJE_TELEFONO_DUPLICADO.format(telefono=telefono)
    if usuario and bd.obtener_usuario_por_nombre(usuario) is not None:
        return MENSAJE_USUARIO_OCUPADO.format(usuario=usuario)
    return ""


def crear_cuenta_paciente(bd, datos, hoy=None):
    """Un paciente nuevo crea su propia cuenta (no requiere sesión).

    `datos`: nombre, apellidos, telefono, correo (opcional),
    fecha_nacimiento (opcional), usuario, contrasena y confirmacion.
    Devuelve {"exito", "mensaje", "id_paciente"}.
    """
    datos = datos or {}
    error = (validar_datos_paciente(datos, hoy)
             or validar_credenciales(datos.get("usuario"), datos.get("contrasena"),
                                     datos.get("confirmacion", datos.get("contrasena"))))
    if error:
        return _resultado(False, error, id_paciente=None)
    limpio = _datos_limpios(datos)
    usuario = datos["usuario"].strip()
    try:
        error = _revisar_duplicados(bd, limpio["telefono"], usuario)
        if error:
            return _resultado(False, error, id_paciente=None)
        id_paciente = bd.insertar_paciente_con_usuario(
            **limpio, nombre_usuario=usuario,
            contrasena_hash=generar_hash(datos["contrasena"]),
        )
    except ErrorIntegridad:
        return _resultado(False, MENSAJE_USUARIO_OCUPADO.format(usuario=usuario),
                          id_paciente=None)
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje, id_paciente=None)
    return _resultado(True, MENSAJE_CUENTA_CREADA.format(nombre=limpio["nombre"]),
                      id_paciente=id_paciente)


def registrar_paciente(bd, sesion, datos, hoy=None):
    """La recepcionista registra a un paciente nuevo.

    Si `datos` trae usuario y contrasena, también le crea su acceso; si no,
    el paciente queda registrado para agendarle citas desde recepción.
    """
    permiso = verificar_permiso(sesion, "registrar_paciente")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"], id_paciente=None)
    datos = datos or {}
    con_acceso = not esta_vacio(datos.get("usuario")) or not esta_vacio(datos.get("contrasena"))
    error = validar_datos_paciente(datos, hoy)
    if not error and con_acceso:
        error = validar_credenciales(datos.get("usuario"), datos.get("contrasena"))
    if error:
        return _resultado(False, error, id_paciente=None)
    limpio = _datos_limpios(datos)
    usuario = datos["usuario"].strip() if con_acceso else None
    try:
        error = _revisar_duplicados(bd, limpio["telefono"], usuario)
        if error:
            return _resultado(False, error, id_paciente=None)
        if con_acceso:
            id_paciente = bd.insertar_paciente_con_usuario(
                **limpio, nombre_usuario=usuario,
                contrasena_hash=generar_hash(datos["contrasena"]),
            )
        else:
            id_paciente = bd.insertar_paciente(**limpio)
    except ErrorIntegridad:
        return _resultado(False, MENSAJE_USUARIO_OCUPADO.format(usuario=usuario),
                          id_paciente=None)
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje, id_paciente=None)
    mensaje = MENSAJE_PACIENTE_REGISTRADO.format(id=id_paciente, **limpio)
    if con_acceso:
        mensaje += f" Usuario: '{usuario}'."
    return _resultado(True, mensaje, id_paciente=id_paciente)


def gestionar_acceso(bd, sesion, id_paciente, usuario, contrasena):
    """La recepcionista crea el acceso de un paciente existente o, si ya
    tiene usuario, le restablece la contraseña (el usuario no cambia)."""
    permiso = verificar_permiso(sesion, "gestionar_accesos")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"])
    try:
        paciente = bd.obtener_paciente(int(id_paciente))
    except (TypeError, ValueError):
        paciente = None
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje)
    if paciente is None:
        return _resultado(False, MENSAJE_PACIENTE_INEXISTENTE)
    nombre = f"{paciente['nombre']} {paciente['apellidos']}"
    try:
        existente = bd.obtener_usuario_de_paciente(paciente["id_paciente"])
        if existente is not None:
            error = validar_credenciales(existente["nombre_usuario"], contrasena)
            if error:
                return _resultado(False, error)
            bd.actualizar_contrasena(existente["id_usuario"], generar_hash(contrasena))
            return _resultado(True, MENSAJE_ACCESO_RESTABLECIDO.format(
                paciente=nombre, usuario=existente["nombre_usuario"]))
        error = validar_credenciales(usuario, contrasena)
        if error:
            return _resultado(False, error)
        usuario = usuario.strip()
        if bd.obtener_usuario_por_nombre(usuario) is not None:
            return _resultado(False, MENSAJE_USUARIO_OCUPADO.format(usuario=usuario))
        bd.insertar_usuario(usuario, generar_hash(contrasena), ROL_PACIENTE,
                            id_paciente=paciente["id_paciente"])
    except ErrorIntegridad:
        return _resultado(False, MENSAJE_USUARIO_OCUPADO.format(usuario=usuario))
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje)
    return _resultado(True, MENSAJE_ACCESO_CREADO.format(paciente=nombre, usuario=usuario))


def listar_pacientes(bd, sesion, busqueda=""):
    """Pacientes para recepción, con su usuario si tienen acceso.

    `busqueda` filtra por nombre, apellidos, teléfono o usuario.
    """
    permiso = verificar_permiso(sesion, "registrar_paciente")
    if not permiso["exito"]:
        return _resultado(False, permiso["mensaje"], pacientes=[])
    try:
        pacientes = bd.listar_pacientes_con_acceso()
    except ErrorBaseDatos as error_bd:
        return _resultado(False, error_bd.mensaje, pacientes=[])
    termino = (busqueda or "").strip().lower()
    if termino:
        pacientes = [
            p for p in pacientes
            if termino in " ".join(str(p.get(c) or "") for c in
                                   ("nombre", "apellidos", "telefono", "nombre_usuario")).lower()
        ]
    return _resultado(True, "", pacientes=pacientes)

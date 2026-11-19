"""Datos de demostración para probar el sistema de extremo a extremo.

Solo se cargan cuando la base no tiene usuarios. Las contraseñas son de
prueba para el entorno local; no son credenciales reales.
"""

from modules.auth_roles import registrar_usuario

ODONTOLOGOS_DEMO = (
    ("Laura", "Peña Núñez", "Ortodoncia"),
    ("Jorge", "Ruiz Campos", "Odontología general"),
)

SERVICIOS_DEMO = (
    ("Valoración inicial", 30, "Revisión general y plan de tratamiento", 350.0),
    ("Limpieza dental", 45, "Profilaxis y eliminación de sarro", 850.0),
    ("Radiografía panorámica", 20, "Ortopantomografía digital", 450.0),
    ("Ajuste de ortodoncia", 30, "Revisión y ajuste de brackets", 600.0),
)

PACIENTES_DEMO = (
    ("Ana", "Pérez Soto", "4771112233", "ana.perez@correo.com"),
    ("Luis", "Gómez Vega", "4774445566", None),
)

# (usuario, contraseña de prueba, rol, índice del paciente u odontólogo)
USUARIOS_DEMO = (
    ("recepcion01", "Recepcion#2026", "recepcionista", None),
    ("paciente01", "Paciente#2026", "paciente", 0),
    ("paciente02", "Paciente#2026", "paciente", 1),
    ("dentista01", "Dentista#2026", "dentista", 0),
    ("dentista02", "Dentista#2026", "dentista", 1),
)


def sembrar_datos_demo(bd):
    """Carga los datos de demostración si la base no tiene usuarios.

    Devuelve True si cargó los datos y False si ya existían.
    """
    if bd.contar_usuarios() > 0:
        return False

    ids_odontologo = [bd.insertar_odontologo(*o) for o in ODONTOLOGOS_DEMO]
    for nombre, duracion, descripcion, precio in SERVICIOS_DEMO:
        bd.insertar_servicio(nombre, duracion, descripcion, precio)
    ids_paciente = [
        bd.insertar_paciente(nombre, apellidos, telefono, correo)
        for nombre, apellidos, telefono, correo in PACIENTES_DEMO
    ]

    for usuario, clave, rol, indice in USUARIOS_DEMO:
        registrar_usuario(
            bd, usuario, clave, rol,
            id_paciente=ids_paciente[indice] if rol == "paciente" else None,
            id_odontologo=ids_odontologo[indice] if rol == "dentista" else None,
        )
    return True

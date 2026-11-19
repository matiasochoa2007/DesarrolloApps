# Orthoimagen Dental · Sistema de citas

Proyecto de **Desarrollo de Aplicaciones y Servicios Virtuales** (Universidad Iberoamericana León).
Equipo: **Matias Ochoa Tirado** y **Mateo Javier Ortega Fernández**.

Sistema de consola en Python para registrar, consultar, modificar, cancelar y eliminar citas de la
clínica, con inicio de sesión por rol (paciente, recepcionista, dentista) y datos guardados en SQLite.

## Requisitos

- Python 3.10 o superior (en Windows se usa el lanzador `py`).
- No hay dependencias externas: solo la biblioteca estándar (`sqlite3`, `hashlib`, `unittest`).

## Cómo ejecutar

Desde la raíz del repositorio:

```powershell
py main.py
```

La primera vez se crea `data/orthoimagen.db` y se cargan datos de demostración.
Para usar otra base, define la variable de entorno `ORTHOIMAGEN_BD` con la ruta del archivo.

### Usuarios de demostración (solo entorno local)

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `recepcion01` | `Recepcion#2026` | recepcionista |
| `paciente01` | `Paciente#2026` | paciente (Ana Pérez Soto) |
| `paciente02` | `Paciente#2026` | paciente (Luis Gómez Vega) |
| `dentista01` | `Dentista#2026` | dentista (Laura Peña Núñez) |
| `dentista02` | `Dentista#2026` | dentista (Jorge Ruiz Campos) |

Se definen en `modules/demo_data.py`. Las contraseñas se guardan con hash PBKDF2-SHA256.

## Cómo ejecutar las pruebas

```powershell
py -m unittest discover -v
```

## Estructura

```
main.py                       Consola: login y menú por rol
config/settings.py            Ruta de la base y parámetros
modules/validation_messages.py  M6 Validación y mensajes (RF-10)
modules/data_access.py        M7 Acceso a datos SQLite (RF-09)
modules/auth_roles.py         M1 Autenticación y roles (RF-11)
modules/service_catalog.py    M5 Catálogo de servicios (RF-08)
modules/availability.py       M3 Disponibilidad (RF-07, RF-02)
modules/appointments.py       M2 Gestión de citas (RF-01)
modules/demo_data.py          Datos de demostración
tests/                        Pruebas unittest por módulo
docs/plan_incrementos.md      Plan de incrementos, ambigüedades y registro de cambios
```

## Incrementos

| Incremento | Tag | Contenido |
|-----------|-----|-----------|
| 1 | `v0.1.0` | Mensajes claros de error (RF-10) |
| 2 | `v0.2.0` | SQLite, inicio de sesión con roles y catálogo de servicios (RF-09, RF-11, RF-08) |
| 3 | `v0.3.0` | Disponibilidad, citas sin empalmes y registro de citas (RF-07, RF-02, RF-01) |

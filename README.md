# Orthoimagen Dental · Sistema de citas

Proyecto de **Desarrollo de Aplicaciones y Servicios Virtuales** (Universidad Iberoamericana León).
Equipo: **Matias Ochoa Tirado** y **Mateo Javier Ortega Fernández**.

Aplicación de escritorio en Python para registrar, consultar, modificar, cancelar y eliminar citas
de la clínica, con inicio de sesión por rol (paciente, recepcionista, dentista) y datos guardados en
SQLite. Incluye también una versión de consola que usa los mismos módulos.

## Requisitos

- Python 3.10 o superior (en Windows se usa el lanzador `py`).
- No hay dependencias externas: solo la biblioteca estándar (`sqlite3`, `hashlib`, `unittest`).

## Cómo ejecutar

**Opción 1 · Ejecutable (sin instalar Python):** descarga `OrthoimagenDental.exe` desde la sección
*Releases* del repositorio y ábrelo con doble clic. La base se crea en una carpeta `data` junto al
`.exe`. Windows SmartScreen puede advertir que el archivo no está firmado: elige *Más información →
Ejecutar de todas formas*.

**Opción 2 · App de escritorio desde el código:**

```powershell
py app_escritorio.py
```

**Opción 3 · Consola:**

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

## Qué puede hacer cada rol

| Rol | Opciones |
|-----|----------|
| Paciente | Catálogo, horarios libres, agendar, ver mis citas, modificar y cancelar mis citas |
| Recepcionista | Catálogo, disponibilidad, registrar para un paciente, ver y filtrar citas, modificar, cancelar y eliminar |
| Dentista | Catálogo y agenda del día |

Reglas principales: un dentista no puede tener dos citas activas a la misma hora (RF-02);
cancelar deja la cita en el historial con estatus "Cancelada" y libera el horario; eliminar
borra el registro y solo lo hace la recepcionista. Horario de atención: bloques de 60 minutos
de 09:00 a 18:00 (supuesto configurable en `config/settings.py`).

## Cómo ejecutar las pruebas

```powershell
py -m unittest discover -v
```

Resultado actual: 157 pruebas, 0 fallidas (incluye 9 de la app de escritorio, que se omiten
automáticamente en equipos sin pantalla).

## Cómo generar el ejecutable

```powershell
powershell -ExecutionPolicy Bypass -File construir_exe.ps1
```

Corre las pruebas, instala PyInstaller en `.venv-build` y deja el archivo en `dist\OrthoimagenDental.exe`.

## Estructura

```
app_escritorio.py             App de escritorio (tkinter): ventanas por rol
main.py                       Consola: login y menú por rol
construir_exe.ps1             Genera el .exe con PyInstaller
assets/                       Ícono de la aplicación
config/settings.py            Ruta de la base y parámetros
modules/validation_messages.py  M6 Validación y mensajes (RF-10)
modules/data_access.py        M7 Acceso a datos SQLite (RF-09)
modules/auth_roles.py         M1 Autenticación y roles (RF-11)
modules/service_catalog.py    M5 Catálogo de servicios (RF-08)
modules/availability.py       M3 Disponibilidad (RF-07, RF-02)
modules/appointments.py       M2 Gestión de citas (RF-01, RF-03, RF-04, RF-05)
modules/agenda.py             M4 Consulta de agenda (RF-06)
modules/demo_data.py          Datos de demostración
tests/                        Pruebas unittest por módulo
docs/especificaciones.md      RF, HU, CA y arquitectura consolidados
docs/guia_explicacion_codigo.md  Qué explica cada integrante y cómo funciona cada módulo
docs/plan_incrementos.md      Plan de incrementos, ambigüedades y registro de cambios
docs/matriz_trazabilidad.md   RF → código → commits → pruebas
docs/bitacora_ia.md           Uso de IA y decisiones del equipo
```

## Incrementos

| Incremento | Tag | Contenido |
|-----------|-----|-----------|
| 1 | `v0.1.0` | Mensajes claros de error (RF-10) |
| 2 | `v0.2.0` | SQLite, inicio de sesión con roles y catálogo de servicios (RF-09, RF-11, RF-08) |
| 3 | `v0.3.0` | Disponibilidad, citas sin empalmes y registro de citas (RF-07, RF-02, RF-01) |
| 4 | `v0.4.0` | Consultar, modificar, cancelar y eliminar citas (RF-06, RF-03, RF-04, RF-05) |
| Entrega final | `v1.0.0` | App de escritorio con ventanas por rol y ejecutable para Windows |

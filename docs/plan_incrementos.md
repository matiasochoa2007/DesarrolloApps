# Plan de incrementos: Orthoimagen Dental

**Equipo:** Matias Ochoa Tirado y Mateo Javier Ortega Fernández
**Materia:** Desarrollo de Aplicaciones y Servicios Virtuales · Universidad Iberoamericana León
**Última actualización:** 19 de noviembre de 2026
**Avance global:** 100 % (11 de 11 RF publicados en GitHub con tag) · RF-12 propuesto en v1.1.0

> **Fuente única del plan:** el documento de especificaciones del proyecto (secciones 5, 6.1, 6.2, 6.3 y 6.4),
> consolidado en [especificaciones.md](especificaciones.md). Todo lo que no aparece ahí se registra como ambigüedad.
>
> Registros relacionados: [matriz de trazabilidad](matriz_trazabilidad.md) · [bitácora de IA](bitacora_ia.md)

## 1. Inventario de requerimientos funcionales

| RF | Descripción breve | Incremento | Tag | Sección del documento | Estado |
|----|-------------------|-----------|-----|-----------------------|--------|
| RF-10 | Mensajes claros de error (HU-15) | 1 | v0.1.0 | Req. §5; HU §6.1; CA §6.2 (CA-45 a CA-47) | Publicado (v0.1.0) |
| RF-09 | Base de datos SQLite (HU-17) | 2 | v0.2.0 | Req. §5; HU §6.1; CA §6.2 (CA-51 a CA-53) | Publicado (v0.2.0) |
| RF-11 | Inicio de sesión con roles (HU-16) | 2 | v0.2.0 | Req. §5; HU §6.1; CA §6.2 (CA-48 a CA-50) | Publicado (v0.2.0) |
| RF-08 | Catálogo de servicios (HU-14) | 2 | v0.2.0 | Req. §5; HU §6.1; CA §6.2 (CA-42 a CA-44) | Publicado (v0.2.0) |
| RF-07 | Consultar y validar disponibilidad (HU-12, HU-13) | 3 | v0.3.0 | Req. §5; HU §6.1; CA §6.2 (CA-36 a CA-41) | Publicado (v0.3.0) |
| RF-02 | Validar citas duplicadas por dentista (HU-03) | 3 | v0.3.0 | Req. §5; HU §6.1; CA §6.2 (CA-07 a CA-09) | Publicado (v0.3.0) |
| RF-01 | Registrar citas, paciente o recepcionista (HU-01, HU-02) | 3 | v0.3.0 | Req. §5; HU §6.1; CA §6.2 (CA-01 a CA-06) | Publicado (v0.3.0) |
| RF-06 | Mostrar citas filtradas (HU-09, HU-10, HU-11) | 4 | v0.4.0 | Req. §5; HU §6.1; CA §6.2 (CA-27 a CA-35) | Publicado (v0.4.0) |
| RF-03 | Modificar citas (HU-04, HU-05) | 4 | v0.4.0 | Req. §5; HU §6.1; CA §6.2 (CA-10 a CA-16) | Publicado (v0.4.0) |
| RF-04 | Cancelar citas (HU-06, HU-07) | 4 | v0.4.0 | Req. §5; HU §6.1; CA §6.2 (CA-17 a CA-23) | Publicado (v0.4.0) |
| RF-05 | Eliminar citas, solo recepción (HU-08) | 4 | v0.4.0 | Req. §5; HU §6.1; CA §6.2 (CA-24 a CA-26) | Publicado (v0.4.0) |
| RF-12 (propuesto) | Registro de pacientes nuevos y gestión de accesos | 1.1 | v1.1.0 | Ver ambigüedad A2 | Publicado; pendiente de aprobación |

Totales del documento: 11 RF, 9 RNF, 17 HU y 53 CA base (57 con criterios de revisión).

## 2. Incrementos

### Incremento 1 · v0.1.0 · rama `master`

| Campo | Respuesta del equipo |
|-------|----------------------|
| Objetivo | El sistema muestra mensajes de error claros al usuario. |
| RF e HU | RF-10 (HU-15), con apoyo a RF-01 (HU-01) |
| Criterios de aceptación | CA-45, CA-46, CA-47 (§6.2) y apoyo a CA-03 |
| Módulos | M6 Validación y mensajes (`modules/validation_messages.py`) |
| Depende de | Ninguno |
| Pruebas mínimas | Normal: un campo vacío (CA-45). Límite: todos vacíos (CA-46). Error: horario ocupado (CA-47). |
| Estado | Cerrado y etiquetado (v0.1.0). 15 pruebas pasan. |

### Incremento 2 · v0.2.0 · rama `incremento-2`

| Campo | Respuesta del equipo |
|-------|----------------------|
| Objetivo | Un usuario inicia sesión con su rol y consulta el catálogo de servicios, con los datos guardados en SQLite. |
| RF e HU | RF-09 (HU-17), RF-11 (HU-16), RF-08 (HU-14) |
| Criterios de aceptación | CA-51 a CA-53 (HU-17), CA-48 a CA-50 (HU-16), CA-42 a CA-44 (HU-14); §6.2 |
| Módulos | M7 Acceso a datos, M1 Autenticación y roles, M5 Catálogo de servicios (reutiliza M6) |
| Depende de | Incremento 1 (RF-10 / M6): reutiliza `esta_vacio` y el estilo de mensajes |
| Pruebas mínimas | Normal: login correcto y catálogo con servicios. Límite: catálogo vacío; paciente que intenta una función de recepción (CA-49). Error: credenciales incorrectas; base no disponible. |
| Archivos | `config/settings.py`, `modules/data_access.py` (M7), `modules/auth_roles.py` (M1), `modules/service_catalog.py` (M5), `modules/demo_data.py`, `main.py` |
| Estado | Cerrado y etiquetado (v0.2.0). Regresión: 55 pruebas, 0 fallidas. |

### Incremento 3 · v0.3.0 · rama `incremento-3`

| Campo | Respuesta del equipo |
|-------|----------------------|
| Objetivo | Un usuario consulta la disponibilidad de un dentista y registra una cita sin que se empalme con otra. |
| RF e HU | RF-07 (HU-12, HU-13), RF-02 (HU-03), RF-01 (HU-01, HU-02) |
| Criterios de aceptación | RF-07: CA-36 a CA-41. RF-02: CA-07 a CA-09. RF-01: CA-01 a CA-06. Reutilizados: CA-45 a CA-47. |
| Módulos | M3 Disponibilidad, M2 Gestión de citas, M6 Validación y mensajes, M7 Acceso a datos |
| Depende de | Incremento 1 (M6) e Incremento 2 (sesión con rol RF-11, SQLite RF-09 y catálogo RF-08) |
| Cierres diferidos | CA-01 (ver la cita en "mis citas", con RF-06) y CA-40 (horario liberado tras cancelar, con RF-04): verificados en el Incremento 4. |
| Archivos | `modules/availability.py` (M3), `modules/appointments.py` (M2), citas en `modules/data_access.py` (M7), `main.py` |
| Estado | Cerrado y etiquetado (v0.3.0). Regresión: 99 pruebas, 0 fallidas. |

### Incremento 4 · v0.4.0 · rama `incremento-4`

| Campo | Respuesta del equipo |
|-------|----------------------|
| Objetivo | Un usuario consulta sus citas filtradas, modifica citas existentes, las cancela liberando el horario, y la recepcionista puede eliminarlas. |
| RF e HU | RF-06 (HU-09, HU-10, HU-11), RF-03 (HU-04, HU-05), RF-04 (HU-06, HU-07), RF-05 (HU-08) |
| Criterios de aceptación | RF-06: CA-27 a CA-35. RF-03: CA-10 a CA-16. RF-04: CA-17 a CA-23. RF-05: CA-24 a CA-26. Reutilizados: CA-45 a CA-47. |
| Módulos | M4 Consulta de agenda, M2 Gestión de citas, M3 Disponibilidad, M1 Autenticación y roles, M6 y M7 |
| Depende de | Incremento 3 (citas y disponibilidad), Incremento 2 (sesión con rol) e Incremento 1 (M6) |
| Pruebas mínimas | Normal: CA-27, CA-30, CA-33, CA-10, CA-14, CA-17, CA-21, CA-24. Límite: CA-28, CA-31, CA-34, CA-11, CA-15, CA-18, CA-22, CA-25. Error: CA-12, CA-13, CA-16, CA-19, CA-20, CA-23, CA-26, CA-29, CA-32, CA-35. |
| Archivos | `modules/agenda.py` (M4), modificar/cancelar/eliminar en `modules/appointments.py` (M2), `modules/data_access.py` (M7), `main.py` |
| Cierres diferidos verificados | CA-01 (`test_agenda.py`) y CA-40 (`test_appointments_cambios.py`) |
| Estado | Cerrado y etiquetado (v0.4.0). Regresión: 148 pruebas, 0 fallidas. |

### Versión 1.1 · v1.1.0 · rama `version-1.1`

| Campo | Respuesta del equipo |
|-------|----------------------|
| Objetivo | Un cliente nuevo puede darse de alta (por sí mismo o en recepción) y un cliente de siempre puede obtener o recuperar su acceso, en una interfaz profesional con manual de usuario. |
| Requerimiento | RF-12 propuesto (ver A2). No modifica RF-01 a RF-11. |
| Módulos | M8 Registro de pacientes (`modules/patients.py`), `interfaz/api.py`, `interfaz/web/`, M7 (alta en una transacción) y M1 (permisos nuevos) |
| Pruebas | `test_patients.py` (17) y `test_api.py` (10); regresión total: 177 pruebas, 0 fallidas |
| Entregables | `OrthoimagenDental.exe` v1.1 y `docs/manual/Manual_Orthoimagen_Dental.pdf` |
| Estado | Cerrado y etiquetado (v1.1.0). |

## 3. Ambigüedades y su resolución

| Requerimiento | Ambigüedad | Resolución del equipo | Confirmado por el profesor |
|---------------|-----------|-----------------------|----------------------------|
| RF-02 | "Mismo horario": ¿hora de inicio o traslape por duración? | Misma hora de inicio (supuesto de la bitácora 6.4). | Pendiente |
| RF-07 | El documento no define el horario de atención ni la duración de cada bloque | Supuesto: bloques de 60 min de 09:00 a 18:00, configurables en `config/settings.py`. | Pendiente |
| RF-04 y RF-05 | No se define la diferencia entre cancelar y eliminar | Cancelar = estatus "Cancelada" (CA-17); eliminar = borrar el registro en la BD (CA-24). | Pendiente |
| A2 | El documento no dice cómo llega al sistema un paciente nuevo, aunque el RNF de usabilidad habla de "un paciente nuevo" y HU-01/HU-02 suponen que el paciente ya existe | Se propone RF-12: auto-registro del paciente y alta y accesos desde recepción, sin duplicar expedientes (el teléfono es único). | Pendiente |
| A1 | Totales distintos entre ChatGPT y el equipo (RNF: 9 vs. sin dato; CA: 57 vs. 53) | El documento final (§6.1 y §6.2) consolida 11 RF, 9 RNF, 17 HU y 53 CA base (57 con criterios de revisión). | n/a |

## 4. Registro de cambios al plan

| Fecha | Cambio | Motivo | Aprobado por |
|-------|--------|--------|--------------|
| 08/11/2026 | Creación del plan inicial de incrementos | Organización del trabajo tras la entrega de requerimientos y arquitectura. | Matias Ochoa / Mateo Ortega |
| 19/11/2026 | Se publica el plan en `docs/` y se etiqueta v0.1.0 sobre `master` | El repositorio solo tenía el commit "Estructura Inicial"; el plan y el tag del Incremento 1 no estaban publicados. | Equipo de desarrollo |
| 19/11/2026 | Cierre del Incremento 2 (v0.2.0) | Roles definidos como paciente, recepcionista y dentista (HU-01 a HU-16); se descarta el rol "Administrador" de la práctica de persistencia porque no aparece en RF-01 a RF-11. | Equipo de desarrollo |
| 19/11/2026 | Cierre del Incremento 3 (v0.3.0) | Se fija el horario de atención como supuesto (bloques de 60 min, 09:00 a 18:00) porque el documento no lo define; RF-02 se refuerza con un índice único en la BD. | Equipo de desarrollo |
| 19/11/2026 | Cierre del Incremento 4 (v0.4.0): RF-06, RF-03, RF-04 y RF-05 | Se completa el 100 % de los RF; se agregan `docs/matriz_trazabilidad.md` y `docs/bitacora_ia.md`. | Equipo de desarrollo |
| 19/11/2026 | Entrega final (v1.0.0): app de escritorio y ejecutable | La interfaz de ventanas cumple el RNF de usabilidad (agendar en 5 pasos) sin agregar funciones fuera de RF-01 a RF-11; usa los mismos módulos que la consola. | Equipo de desarrollo |
| 19/11/2026 | Versión 1.1 (v1.1.0): RF-12 propuesto, interfaz rediseñada y manual de usuario | Responder qué pasa con un cliente nuevo y con los clientes de siempre sin usuario; la interfaz tkinter se sustituyó por una ventana nativa con diseño profesional. | Equipo de desarrollo (RF-12 pendiente del profesor) |

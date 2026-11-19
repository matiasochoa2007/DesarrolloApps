# Matriz de trazabilidad · Orthoimagen Dental

Cada fila une un requerimiento con la sección del documento de especificaciones de donde sale, el
código que lo implementa, los commits y la prueba que lo demuestra.

Comando de regresión (desde la raíz del repositorio): `py -m unittest discover -v`
Resultado al cierre de v0.4.0: **148 pruebas ejecutadas, 0 fallidas** (Windows 11, Python 3.14).
Resultado en la entrega final v1.0.0: **157 pruebas ejecutadas, 0 fallidas**.

## Requerimientos funcionales

| RF / HU | Sección | Inc. | Módulo y archivos | Commits | Tag | Pruebas (archivo y CA) | Estado |
|---------|---------|------|-------------------|---------|-----|------------------------|--------|
| RF-10 / HU-15 | Req. §5; HU §6.1; CA §6.2 | 1 | M6 `modules/validation_messages.py` | f52fb54, 6e5abdf, 6b226fe | v0.1.0 | `test_validation_messages.py`: CA-45, CA-46, CA-47, CA-03 (15 pruebas) | Terminado |
| RF-09 / HU-17 | Req. §5; HU §6.1; CA §6.2 | 2 | M7 `modules/data_access.py`, `config/settings.py` | 1290db7, 7d69759 | v0.2.0 | `test_data_access.py`: CA-51, CA-52, CA-53 | Terminado |
| RF-11 / HU-16 | Req. §5; HU §6.1; CA §6.2 | 2 | M1 `modules/auth_roles.py`, `main.py` | 96991cc, 5b3bbab | v0.2.0 | `test_auth_roles.py`: CA-48, CA-49, CA-50; `test_main.py` | Terminado |
| RF-08 / HU-14 | Req. §5; HU §6.1; CA §6.2 | 2 | M5 `modules/service_catalog.py` | 833610d | v0.2.0 | `test_service_catalog.py`: CA-42, CA-43, CA-44 | Terminado |
| RF-07 / HU-12, HU-13 | Req. §5; HU §6.1; CA §6.2 | 3 | M3 `modules/availability.py` | aab642d | v0.3.0 | `test_availability.py`: CA-36 a CA-41 | Terminado |
| RF-02 / HU-03 | Req. §5; HU §6.1; CA §6.2 | 3 | M3 `modules/availability.py`, índice único en M7 | 71d697f, aab642d | v0.3.0 | `test_availability.py` y `test_appointments.py`: CA-07, CA-08, CA-09 | Terminado |
| RF-01 / HU-01, HU-02 | Req. §5; HU §6.1; CA §6.2 | 3 | M2 `modules/appointments.py`, `main.py` | 80ffe12, cd596bb | v0.3.0 | `test_appointments.py`: CA-01 a CA-06; CA-01 diferido en `test_agenda.py` | Terminado |
| RF-06 / HU-09, HU-10, HU-11 | Req. §5; HU §6.1; CA §6.2 | 4 | M4 `modules/agenda.py`, `main.py` | 1d3a2f7, 8ccb54a | v0.4.0 | `test_agenda.py`: CA-27 a CA-35 | Terminado |
| RF-03 / HU-04, HU-05 | Req. §5; HU §6.1; CA §6.2 | 4 | M2 `modules/appointments.py` | af405c2 | v0.4.0 | `test_appointments_cambios.py`: CA-10 a CA-16 | Terminado |
| RF-04 / HU-06, HU-07 | Req. §5; HU §6.1; CA §6.2 | 4 | M2 `modules/appointments.py` | f051da9 | v0.4.0 | `test_appointments_cambios.py`: CA-17 a CA-23; CA-40 diferido | Terminado |
| RF-05 / HU-08 | Req. §5; HU §6.1; CA §6.2 | 4 | M2 `modules/appointments.py` | 4f28be2 | v0.4.0 | `test_appointments_cambios.py`: CA-24, CA-25, CA-26 | Terminado |

## Pruebas por archivo

| Archivo | Módulo | Pruebas |
|---------|--------|---------|
| `tests/test_validation_messages.py` | M6 | 15 |
| `tests/test_data_access.py` | M7 | 19 |
| `tests/test_auth_roles.py` | M1 | 18 |
| `tests/test_service_catalog.py` | M5 | 5 |
| `tests/test_availability.py` | M3 | 16 |
| `tests/test_appointments.py` | M2 (registro) | 19 |
| `tests/test_agenda.py` | M4 | 18 |
| `tests/test_appointments_cambios.py` | M2 (modificar, cancelar, eliminar) | 28 |
| `tests/test_main.py` | Consola de extremo a extremo | 10 |
| `tests/test_app_escritorio.py` | App de escritorio de extremo a extremo | 9 |
| **Total** | | **157** |

## Nota sobre los criterios de aceptación

El texto de cada CA está en [especificaciones.md](especificaciones.md) (sección 5) y cada prueba lleva
el número de CA en su nombre (por ejemplo `test_ca24_recepcionista_elimina...`).

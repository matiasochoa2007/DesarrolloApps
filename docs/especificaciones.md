# Especificación consolidada · Orthoimagen Dental

**Equipo:** Matias Ochoa Tirado y Mateo Javier Ortega Fernández
**Materia:** Desarrollo de Aplicaciones y Servicios Virtuales · Universidad Iberoamericana León

> **Origen de este documento.** Consolida en un solo lugar lo que aparece en los documentos del
> curso: el plan de incrementos, la práctica del primer módulo, la práctica de persistencia y la
> evaluación del segundo parcial. Los identificadores (RF, HU, CA y M) son los del documento de
> especificaciones original. El texto de cada CA se redactó a partir de las pruebas mínimas del
> plan; si el original dice algo distinto, manda el original y se registra el cambio en el plan.

## 1. Problema y usuarios

La clínica no tiene un buen método para registrar, modificar y eliminar citas, lo que genera
desorden y pérdida de datos. El sistema centraliza las citas en una base de datos y aplica las
reglas de agenda.

| Usuario | Necesidad principal |
|---------|---------------------|
| Paciente | Ver horarios libres, agendar, consultar, modificar y cancelar sus citas sin llamar a la clínica. |
| Recepcionista | Registrar, filtrar, modificar, cancelar y eliminar las citas de cualquier paciente. |
| Dentista | Consultar su agenda del día. |

Fuera de alcance: pagos en línea, recordatorios, registro de pacientes desde el sistema y rol
de administrador.

## 2. Requerimientos funcionales (§5)

| ID | Requerimiento | HU | CA | Módulos |
|----|---------------|----|----|---------|
| RF-01 | Registrar citas por el paciente o por la recepcionista | HU-01, HU-02 | CA-01 a CA-06 | M2, M3, M6 |
| RF-02 | Impedir que un dentista tenga dos citas en el mismo horario | HU-03 | CA-07 a CA-09 | M3, M7 |
| RF-03 | Modificar citas | HU-04, HU-05 | CA-10 a CA-16 | M2, M3 |
| RF-04 | Cancelar citas | HU-06, HU-07 | CA-17 a CA-23 | M2, M3 |
| RF-05 | Eliminar citas (solo recepción) | HU-08 | CA-24 a CA-26 | M2 |
| RF-06 | Mostrar citas filtradas | HU-09, HU-10, HU-11 | CA-27 a CA-35 | M4 |
| RF-07 | Consultar y validar disponibilidad | HU-12, HU-13 | CA-36 a CA-41 | M3 |
| RF-08 | Catálogo de servicios | HU-14 | CA-42 a CA-44 | M5 |
| RF-09 | Guardar los datos en una base SQLite | HU-17 | CA-51 a CA-53 | M7 |
| RF-10 | Mostrar mensajes de error claros | HU-15 | CA-45 a CA-47 | M6 |
| RF-11 | Inicio de sesión con roles | HU-16 | CA-48 a CA-50 | M1 |

## 3. Requerimiento no funcional de referencia

El documento original define 9 RNF. El que se usa en las evaluaciones del curso es:

- **Usabilidad:** un paciente nuevo debe poder agendar una cita en máximo 2 minutos y 5 pasos.
  Se comprueba con 5 usuarios reales, cronometrando cada intento. En la app de escritorio el
  recorrido es: iniciar sesión → elegir dentista → elegir fecha → elegir horario y servicio →
  confirmar.

## 4. Historias de usuario (§6.1)

| HU | Como… | quiero… | para… |
|----|-------|---------|-------|
| HU-01 | paciente | registrar mi cita eligiendo fecha y hora disponibles | no tener que llamar a la clínica |
| HU-02 | recepcionista | registrar una cita a nombre de un paciente | atender a quien llama o acude en persona |
| HU-03 | sistema | impedir que un dentista tenga dos citas en el mismo horario | evitar empalmes |
| HU-04 | paciente | modificar mi cita | ajustarla a mi disponibilidad |
| HU-05 | recepcionista | modificar cualquier cita, incluso el dentista | reorganizar la agenda |
| HU-06 | paciente | cancelar mi cita | liberar el horario si no puedo asistir |
| HU-07 | recepcionista | cancelar una cita | registrar avisos de los pacientes |
| HU-08 | recepcionista | eliminar una cita | depurar registros erróneos |
| HU-09 | paciente | ver mis citas | saber cuándo y con quién tengo cita |
| HU-10 | recepcionista | filtrar citas por día, dentista o paciente | organizar el trabajo |
| HU-11 | dentista | ver mi agenda del día | prepararme para mis pacientes |
| HU-12 | paciente | consultar los horarios libres de un dentista | elegir cuándo agendar |
| HU-13 | recepcionista | consultar la disponibilidad de un dentista | ofrecer horarios por teléfono |
| HU-14 | usuario | consultar el catálogo de servicios | saber qué ofrece la clínica, su duración y precio |
| HU-15 | usuario | recibir mensajes claros cuando falten datos o haya conflicto de horario | saber cómo corregirlo |
| HU-16 | usuario | iniciar sesión con mi rol | ver solo lo que me corresponde |
| HU-17 | clínica | que los datos se guarden en una base | no perder información al cerrar el sistema |

## 5. Criterios de aceptación (§6.2)

Formato abreviado: caso → resultado esperado. Entre paréntesis, el tipo de prueba.

**RF-01 · Registrar citas**
- CA-01 (normal): el paciente registra su cita en un horario libre → se guarda como "Programada" y aparece en "mis citas".
- CA-02 (límite): el paciente registra en el último horario del día sin motivo → se guarda; el motivo es opcional.
- CA-03 (error): falta un dato obligatorio → no se guarda y el mensaje nombra el campo (CA-45).
- CA-04 (normal): la recepcionista registra una cita a nombre de un paciente → se guarda con ese paciente.
- CA-05 (límite): la recepcionista no indica el paciente → el mensaje pide el campo "paciente".
- CA-06 (error): el paciente indicado no existe → mensaje "El paciente seleccionado no existe".

**RF-02 · Sin citas duplicadas por dentista**
- CA-07 (normal): dos citas del mismo dentista a horas distintas → ambas se guardan.
- CA-08 (límite): misma hora con otro dentista → se permite.
- CA-09 (error): mismo dentista, misma fecha y hora de inicio → se rechaza con el mensaje de CA-47.

**RF-03 · Modificar citas**
- CA-10 (normal): el paciente cambia fecha y hora a un horario libre → se guarda como "Reprogramada" y el horario anterior queda libre.
- CA-11 (límite): cambiar solo el servicio → no choca consigo misma.
- CA-12 (error): mover a un horario ocupado → mensaje de CA-47 y la cita no cambia.
- CA-13 (error): el paciente intenta modificar una cita ajena → se rechaza.
- CA-14 (normal): la recepcionista cambia el dentista → se guarda y el horario del dentista anterior queda libre.
- CA-15 (límite): mover una cita a un horario liberado por una cancelación → se permite.
- CA-16 (error): modificar dejando un campo vacío → mensaje que nombra el campo.

**RF-04 · Cancelar citas**
- CA-17 (normal): el paciente cancela su cita → estatus "Cancelada", se conserva en el historial y el horario queda libre.
- CA-18 (límite): cancelar la única cita del día de un dentista → su día queda completamente libre.
- CA-19 (error): cancelar una cita ya cancelada → mensaje "ya está cancelada".
- CA-20 (error): el paciente intenta cancelar una cita ajena → se rechaza.
- CA-21 (normal): la recepcionista cancela cualquier cita → estatus "Cancelada".
- CA-22 (límite): reservar el horario recién cancelado → se permite.
- CA-23 (error): cancelar una cita que no existe o ya fue eliminada → mensaje "no existe".

**RF-05 · Eliminar citas**
- CA-24 (normal): la recepcionista elimina una cita → el registro se borra de la base y el horario queda libre.
- CA-25 (límite): eliminar una cita cancelada → se permite y desaparece del historial.
- CA-26 (error): un paciente o dentista intenta eliminar, o la cita no existe → se rechaza con mensaje claro.

**RF-06 · Citas filtradas**
- CA-27 (normal): el paciente ve sus citas ordenadas por fecha y hora.
- CA-28 (límite): paciente sin citas → aviso "No tiene citas registradas".
- CA-29 (error): el paciente pide las citas de otro → se rechaza.
- CA-30 (normal): la recepcionista filtra por día, dentista, paciente o combinaciones.
- CA-31 (límite): filtro sin resultados → aviso.
- CA-32 (error): fecha inválida o paciente/dentista inexistente → mensaje claro.
- CA-33 (normal): el dentista ve sus citas activas del día.
- CA-34 (límite): día sin citas → aviso.
- CA-35 (error): el dentista pide la agenda de otro → se rechaza.

**RF-07 · Disponibilidad**
- CA-36 (normal): el paciente ve los horarios libres de un dentista en una fecha.
- CA-37 (límite): día completamente ocupado → aviso "no tiene horarios libres".
- CA-38 (error): fecha inválida o pasada → mensaje claro.
- CA-39 (normal): la recepcionista ve horarios libres y ocupados.
- CA-40 (límite): un horario cancelado vuelve a aparecer como libre.
- CA-41 (error): dentista inexistente o inactivo → mensaje claro.

**RF-08 · Catálogo de servicios**
- CA-42 (normal): se listan los servicios con duración y precio.
- CA-43 (límite): catálogo vacío → aviso.
- CA-44 (error): base no disponible → mensaje claro.

**RF-10 · Mensajes de error**
- CA-45 (normal): falta un campo → el mensaje nombra ese campo.
- CA-46 (límite): faltan todos → el mensaje los lista todos.
- CA-47 (error): horario ocupado → "El horario seleccionado no está disponible. Por favor, elija un horario diferente."

**RF-11 · Inicio de sesión con roles**
- CA-48 (normal): credenciales correctas → inicia sesión con su rol.
- CA-49 (límite): un paciente intenta una función de recepción → se rechaza.
- CA-50 (error): credenciales incorrectas o vacías → mensaje que no revela cuál dato falló.

**RF-09 · Base de datos**
- CA-51 (normal): guardar, cerrar, reabrir y leer → los datos siguen ahí.
- CA-52 (límite): varias filas se guardan y se leen en orden.
- CA-53 (error): base no disponible → mensaje claro, sin cerrar la aplicación.

## 6. Arquitectura modular (§6.3)

| Módulo | Archivo | Responsabilidad | RF |
|--------|---------|-----------------|----|
| M1 Autenticación y roles | `modules/auth_roles.py` | Login con hash PBKDF2 y permisos por rol | RF-11 |
| M2 Gestión de citas | `modules/appointments.py` | Registrar, modificar, cancelar y eliminar | RF-01, RF-03, RF-04, RF-05 |
| M3 Disponibilidad | `modules/availability.py` | Horarios libres, validación de fecha/hora e indicador de ocupado | RF-07, RF-02 |
| M4 Consulta de agenda | `modules/agenda.py` | Citas por paciente, día, dentista | RF-06 |
| M5 Catálogo de servicios | `modules/service_catalog.py` | Lista de servicios | RF-08 |
| M6 Validación y mensajes | `modules/validation_messages.py` | Campos obligatorios y mensajes de error | RF-10 |
| M7 Acceso a datos | `modules/data_access.py` | Único módulo con SQL; SQLite | RF-09 |

Interfaces: `app_escritorio.py` (ventanas) y `main.py` (consola). Ninguna contiene reglas de
negocio: solo capturan datos, llaman a los módulos y muestran sus mensajes.

## 7. Persistencia (práctica de persistencia)

SQLite con 5 tablas: `paciente`, `odontologo`, `servicio`, `usuario` y `cita`. Relaciones 1 a N
de paciente, odontólogo y servicio hacia cita. Estatus de cita: Programada, Reprogramada,
Cancelada y Atendida. Las contraseñas se guardan con hash, nunca en texto plano.

## 8. Supuestos (bitácora 6.4) y ambigüedades

Ver la sección 3 de [plan_incrementos.md](plan_incrementos.md).

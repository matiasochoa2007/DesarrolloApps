# Guía para explicar el código · Orthoimagen Dental

La definición de terminado pide que **cada integrante pueda explicar una parte del código**. Esta guía
reparte los módulos y resume lo que hay que saber de cada uno. Para practicar, lean el archivo, corran
sus pruebas y respondan las preguntas de control sin mirar.

| Integrante | Partes que explica | Pruebas que debe saber correr |
|------------|--------------------|-------------------------------|
| **Matias Ochoa Tirado** | M6 Validación y mensajes, M3 Disponibilidad, M2 Gestión de citas (registrar y modificar), M1 Autenticación y roles | `test_validation_messages`, `test_availability`, `test_appointments`, `test_auth_roles` |
| **Mateo Javier Ortega Fernández** | M7 Acceso a datos, M5 Catálogo, M4 Consulta de agenda, M2 (cancelar y eliminar), interfaces (`app_escritorio.py`, `main.py`), Git y el `.exe` | `test_data_access`, `test_service_catalog`, `test_agenda`, `test_appointments_cambios`, `test_app_escritorio`, `test_main` |

Comando para una sola parte: `py -m unittest tests.test_availability -v`
Comando para todo: `py -m unittest discover -v`

## Idea general (los dos deben poder decirla)

1. Las **interfaces** (ventanas y consola) solo piden datos y muestran mensajes; no deciden nada.
2. Las **reglas** viven en los módulos M1 a M6.
3. **Solo M7 escribe SQL.** Si mañana cambiamos SQLite por MySQL, solo se toca `data_access.py`.
4. Todas las funciones devuelven un diccionario con `exito` (o `valido`) y `mensaje`, así las
   interfaces siempre saben qué mostrar.

Flujo de agendar una cita:

```
Ventana → registrar_cita (M2)
            ├─ verificar_permiso (M1)       ¿el rol puede registrar?
            ├─ validar_cita (M6)            ¿faltan campos?
            ├─ validar_fecha / validar_hora (M3)
            ├─ ¿existen dentista, servicio y paciente? (M7)
            ├─ horario_ocupado (M3) → validar_cita (M6)  mensaje CA-47
            └─ insertar_cita (M7)           índice único como última defensa
```

---

## Parte de Matias

### M6 · `modules/validation_messages.py` (RF-10)
- `esta_vacio`: None, "" o solo espacios cuentan como vacío.
- `obtener_campos_faltantes`: revisa fecha, hora, dentista, servicio y, si `requiere_paciente`, paciente; siempre en ese orden.
- `validar_cita`: primero campos faltantes, después horario ocupado. **M6 no calcula disponibilidad**: recibe el indicador de M3.

**Preguntas de control.** ¿Por qué `requiere_paciente` es un parámetro y no el rol? → Para que M6 no dependa de M1. ¿Qué pasa si faltan campos y además el horario está ocupado? → Se reportan los campos.

### M3 · `modules/availability.py` (RF-07 y RF-02)
- `horarios_del_dia`: bloques de 60 min de 09:00 a 18:00 (último inicio 17:00), configurables en `config/settings.py`.
- `validar_fecha` (formato AAAA-MM-DD y que no sea pasada) y `validar_hora` (que sea un inicio de bloque).
- `horario_ocupado`: le pregunta a M7 las horas con cita **no cancelada** de ese dentista ese día. `excluir_id_cita` evita que una cita choque consigo misma al modificarla (CA-11).
- `consultar_disponibilidad`: el paciente ve solo horarios libres; la recepcionista también los ocupados.

**Preguntas de control.** ¿Qué significa "mismo horario" en RF-02? → La misma hora de inicio (ambigüedad resuelta en el plan). ¿Por qué un horario cancelado vuelve a estar libre? → Porque `horas_ocupadas` ignora el estatus "Cancelada" (CA-40).

### M2 (parte 1) · `modules/appointments.py`: `registrar_cita` y `modificar_cita` (RF-01, RF-03)
- El paciente registra a su nombre: el sistema toma su `id_paciente` de la sesión, aunque mande otro.
- La recepcionista debe indicar el paciente (`requiere_paciente=True`).
- `modificar_cita` mezcla los datos actuales con los cambios y vuelve a pasar por las mismas validaciones. Si cambia fecha, hora o dentista, el estatus pasa a "Reprogramada". Solo recepción puede cambiar de dentista (CA-14).
- Si dos personas guardan el mismo horario al mismo tiempo, el índice único de la base lanza `ErrorIntegridad` y se muestra el mensaje de CA-47.

**Preguntas de control.** ¿Cómo se evita que un paciente modifique una cita ajena? → `obtener_cita_autorizada` compara el `id_paciente` de la cita con el de la sesión (CA-13).

### M1 · `modules/auth_roles.py` (RF-11)
- Contraseñas con **PBKDF2-SHA256 + sal aleatoria**: se guarda `pbkdf2_sha256$iteraciones$sal$hash`, nunca la contraseña.
- `verificar_contrasena` usa `hmac.compare_digest` (comparación en tiempo constante).
- `iniciar_sesion` da el mismo mensaje si falla el usuario o la contraseña, para no revelar cuál existe.
- `PERMISOS` es la matriz acción → roles. `verificar_permiso` la consulta (CA-49).

**Preguntas de control.** ¿Por qué la misma contraseña genera hashes distintos? → Por la sal. ¿Dónde se decide que un paciente no puede eliminar? → En `PERMISOS["eliminar_cita"]`.

---

## Parte de Mateo

### M7 · `modules/data_access.py` (RF-09)
- Clase `BaseDatos`: abre la conexión, activa llaves foráneas y crea las 5 tablas con `CREATE TABLE IF NOT EXISTS` (no borra datos).
- Convierte cualquier error de SQLite en `ErrorBaseDatos` con un mensaje claro (CA-53), y los datos duplicados o referencias inválidas en `ErrorIntegridad`.
- Índice único parcial `ux_cita_odontologo_horario` sobre (dentista, fecha, hora) **solo para citas no canceladas**: es la regla RF-02 dentro de la base.
- Consultas con `?` (parámetros), nunca concatenando texto del usuario: evita inyección SQL.

**Preguntas de control.** ¿Cómo se prueba que los datos persisten? → `test_ca51`: guarda, cierra, reabre y lee. ¿Qué pasa si la base no está disponible? → Cada módulo atrapa `ErrorBaseDatos` y devuelve el mensaje; la app no se cierra.

### M5 · `modules/service_catalog.py` (RF-08)
- `consultar_catalogo` devuelve los servicios ordenados; si no hay, un aviso (CA-43); si falla la base, error (CA-44).

### M4 · `modules/agenda.py` (RF-06)
- `mis_citas` (paciente, CA-27 a CA-29), `filtrar_citas` (recepción; filtros vacíos no se aplican; permite fechas pasadas para historial, CA-30 a CA-32) y `agenda_dentista` (solo citas activas del día del propio dentista, CA-33 a CA-35).

### M2 (parte 2) · `cancelar_cita` y `eliminar_cita` (RF-04, RF-05)
- **Cancelar** cambia el estatus a "Cancelada": la cita queda en el historial y el horario se libera.
- **Eliminar** borra el registro de la base; solo la recepcionista. La interfaz pide confirmación.
- Cancelar una cita ya cancelada o inexistente da un mensaje claro (CA-19, CA-23).

**Preguntas de control.** ¿Por qué existen las dos operaciones? → Ambigüedad RF-04/RF-05 resuelta en el plan: cancelar conserva el historial, eliminar depura registros erróneos.

### Interfaces y entrega
- `app_escritorio.py`: una pestaña por función según el rol. Agendar tiene los 5 pasos numerados del RNF de usabilidad. Los mensajes de M6 aparecen en la barra inferior: rojo = error, ámbar = aviso, verde = éxito.
- `main.py`: la misma lógica en consola.
- `construir_exe.ps1`: corre las pruebas y genera el `.exe` con PyInstaller. Cuando corre como `.exe`, la base se guarda junto al ejecutable (`config/settings.py`).
- Git: una rama por incremento (`incremento-2`, `-3`, `-4`), un commit por tarea con formato `tipo(RF-XX): descripción`, merge a `master` y un tag por incremento (`v0.1.0` a `v0.4.0`, `v1.0.0` para la entrega final).

---

## Reflexión individual (la escribe cada quien)

La guía del curso pide responder con sus propias palabras:

1. ¿Qué tareas del incremento puede explicar?
2. ¿Qué diferencia encontró entre lo planeado y lo construido, y por qué?

Diferencias reales que pueden usar como punto de partida: el plan marcaba incrementos como publicados
y el repositorio no los tenía; el horario de atención no estaba en la especificación; la práctica de
persistencia proponía un rol "Administrador" y que eliminar fuera igual a cancelar; M6 no validaba
el formato de fecha y hora, y se resolvió en M3.

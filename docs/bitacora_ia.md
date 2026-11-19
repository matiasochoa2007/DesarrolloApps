# Bitácora de uso de IA · Orthoimagen Dental

Regla del curso: ChatGPT analiza y documenta, Claude desarrolla y prueba, y el equipo decide y verifica.

| Fecha | Herramienta | Prompt o tarea | Qué se aceptó | Qué se modificó o rechazó, y por qué |
|-------|-------------|----------------|---------------|--------------------------------------|
| 22/10/2026 | ChatGPT | Diseño de requerimientos y arquitectura | Módulo de validación independiente | Se rechazó un sistema de pagos en línea: está fuera del alcance (RF-01 a RF-11) y la clínica ya tiene su propio control de pagos. |
| 03/11/2026 | Gemini / Claude | Práctica del primer módulo: M6 Validación y mensajes | `validar_cita` con formato fijo (`valido`, `campos_faltantes`, `mensaje`), parámetro `requiere_paciente` y prioridad de campos faltantes sobre horario ocupado | Se quitó la validación de disponibilidad de M6 (le toca a M3); el paciente solo es obligatorio cuando registra la recepcionista. |
| 05/11/2026 | ChatGPT | Práctica de persistencia: decisión y diseño de BD | SQLite con 5 tablas (paciente, odontologo, servicio, usuario, cita) y diccionario de datos | Se corrigieron los RF asignados a cada tabla (p. ej. usuario → RF-11, no RF-08) y el rol "Administrador" se sustituyó por paciente, recepcionista y dentista. |
| 08/11/2026 | ChatGPT | Fase A (A1 a A4): inventario y plan de incrementos | Inventario de 11 RF, 4 incrementos y ambigüedades de RF-02 y RF-04/RF-05 | Se corrigieron los totales (RNF 9, CA 53 base) contra el conteo del equipo. |
| 19/11/2026 | Claude Code | Entrega final: especificación consolidada, app de escritorio, ejecutable y guía de explicación | `app_escritorio.py` (tkinter), 9 pruebas de extremo a extremo, `construir_exe.ps1`, `docs/especificaciones.md`, `docs/guia_explicacion_codigo.md` y release v1.0.0 | No se agregaron funciones nuevas: la app usa los mismos módulos. La reflexión individual no la escribe la IA; cada integrante la redacta con la guía. |
| 19/11/2026 | Claude Code | Fase B y C de los incrementos 2, 3 y 4 directamente en el repositorio | Módulos M7, M1, M5, M3, M2 y M4, consola por rol, 133 pruebas nuevas, un commit por tarea, ramas `incremento-N`, merge a `master` y tags v0.1.0 a v0.4.0 | Se corrigieron discrepancias entre los documentos y el repositorio (ver "Decisiones" abajo). |

## Decisiones y correcciones de la sesión del 19/11/2026

1. **El repositorio no tenía lo que decía el plan.** GitHub solo tenía el commit "Estructura Inicial"; no existían las ramas `incremento-2/3`, ni los tags v0.1.0 a v0.3.0 marcados como "Publicado". Se construyeron y publicaron todos con commits reales.
2. **M6 original conservado.** El reporte de avance pedía sustituir un M6 reconstruido por el original; el que está en el repositorio (commit f52fb54) es el original y no se modificó su lógica, solo la ruta de ejecución en el docstring de las pruebas.
3. **`__init__.py` agregados** en `config/`, `modules/` y `tests/` para que `py -m unittest discover` ejecute la regresión completa (sin ellos unittest no encuentra las pruebas).
4. **Rama principal:** las guías dicen `main`, pero el repositorio usa `master`; se trabajó sobre `master`.
5. **Roles:** paciente, recepcionista y dentista (según HU-01 a HU-16). La práctica de persistencia mencionaba "Administrador", que no está en RF-01 a RF-11.
6. **Cancelar vs. eliminar:** cancelar = estatus "Cancelada" (se conserva el historial); eliminar = borrar el registro y solo lo hace la recepcionista. La práctica de persistencia proponía que eliminar fuera cancelar; se siguió la resolución del plan.
7. **Horario de atención:** el documento no lo define; se usó el supuesto de bloques de 60 minutos de 09:00 a 18:00 (configurable). Queda registrado como ambigüedad para confirmar con el profesor.
8. **RF-02 reforzado en la base:** además de la validación en M3, un índice único parcial impide dos citas activas del mismo dentista a la misma hora, incluso si dos usuarios guardan al mismo tiempo.
9. **Validación de formato de fecha y hora:** estaba en el backlog de M6; se implementó en M3 (`validar_fecha`, `validar_hora`) para no cambiar el alcance de M6.

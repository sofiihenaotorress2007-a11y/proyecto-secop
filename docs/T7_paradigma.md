# T7 · Decisión de paradigma del proyecto

**Equipo:** «pendiente — se completa por fuera de este borrador»
**Integrantes:** «pendiente — se completa por fuera de este borrador»
**Proyecto:** SECOP II — Contratos Electrónicos
**Fecha:** «AAAA-MM-DD»
**Curso:** IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean

> Primer ladrillo del documento de arquitectura del hito de la sesión 8. Verificación por criterio de aceptación, no por rúbrica.

---

## 0. Supuestos declarados

- **Supuesto 1.** Las cifras de volumen y frecuencia de esta decisión se toman de `docs/ficha_tecnica.md` (T1): dataset completo ≈ 5.900.000 filas / ≈ 4,5 GB estimados, con conteos mensuales observados en la muestra de trabajo entre 3.835 y 4.715 contratos/mes (≈ 130-155 contratos/día). El portal declara actualización "continua", pero esa frecuencia **no fue verificada directamente** (requiere dos descargas en fechas distintas, pendiente según la propia ficha técnica). Se usa la frecuencia declarada como cota superior de lo posible en el origen, no como la frescura que cada requisito exige.
- **Supuesto 2.** Se descarta el requisito de tablero/alerta de monitoreo (antes R4) porque no está implementado y, según `docs/T6_formato.md`, el patrón de acceso real y ya medido del proyecto es "escritura rara, lectura frecuente": nada de lo construido hasta ahora exige frescura de minutos u horas. Los tres requisitos que quedan (R1-R3) son honestamente lotes, con evidencia real en el repositorio, y no se fuerza un cuarto requisito casi-real solo para tener un caso de flujo.
- **Supuesto 3.** La ingesta incremental por API SODA (R2) se declara en `ficha_tecnica.md` como mecanismo previsto para las sesiones 12-13, todavía no construido; se documenta aquí como decisión de arquitectura anticipada, no como algo ya en producción.
- **Supuesto 4.** Al no quedar ningún requisito con necesidad real de flujo o casi-real, la Parte C no puede defender literalmente "el requisito que exige segundos" ni "por qué el híbrido cuesta menos que todo flujo", porque no hay componente de flujo en este proyecto tal como está construido hoy. Se reformula la defensa para responder a la objeción real que sí aplica: por qué conviene mantener varias cadencias de lote separadas (diaria para R2, mensual para R1, bajo demanda para R3) en vez de consolidarlas en un único lote grande. **Esta desviación del enunciado literal debe confirmarse con el profesor o el equipo antes de entregar**; si el criterio de aceptación exige un requisito de flujo real, hay que reconsiderar e incluir uno genuino en el alcance del proyecto, no uno inventado.

---

## Parte A · Tabla de asignación de paradigma

| Requisito | Frescura exigida | Volumen por ciclo | Paradigma | Justificación en una frase |
|---|---|---|---|---|
| R1 · Ingesta cruda del dataset completo al lago (capa raw) | Días | ≈ 4,5 GB / ≈ 5,9 M registros por corrida completa | Lotes | Es un snapshot que alimenta el lago; nadie necesita ver el contrato en el segundo en que se publica para esta capa de acumulación |
| R2 · Ingesta incremental por rango de fechas (API SODA) para mantener el lago al día | Días | Cientos de registros por día (≈ 130-155 contratos/día según la muestra) | Lotes | Una corrida diaria alcanza a capturar la publicación real del origen; no hay costo de negocio por un día de rezago en sincronizar el lago |
| R3 · Análisis histórico y agregados de tendencia (por entidad, sector, monto) | Días | Todo el histórico acumulado por corrida (millones de registros), ejecutado punto en el tiempo | Lotes | Un agregado de tendencia no cambia por tener los datos de hoy en vez de los de ayer; el lote es más barato y su lógica es de por sí recalculable sobre todo el histórico |

**Paradigma del proyecto en conjunto:** Por lotes, sin componente de flujo ni casi-real. Los tres requisitos —ingesta cruda, ingesta incremental y análisis histórico— comparten el mismo patrón ya medido en `docs/T6_formato.md`: escritura rara, lectura frecuente. Ninguno tiene un usuario esperando una respuesta en el instante en que el dato se publica en el origen, así que no hay ningún caso real dentro del proyecto que hoy justifique pagar por flujo (ver Supuesto 2 y Supuesto 4 sobre esta decisión).

---

## Parte B · Compromiso del teorema CAP

- **Requisito sobre el que se decide:** R1 (ingesta cruda del dataset completo al lago). Es el único de los tres con evidencia real de ejecución contra infraestructura de red (MinIO): `docs/T6_formato.md` documenta que el script `src/refinar/convertir_parquet.py` lee de `cruda` vía `s3.download_file`, y `lago-equipo/EVIDENCIA_T5.md` confirma la escritura real al lago. Ahí es donde una partición de red entre el proceso de ingesta y MinIO es un escenario concreto, no hipotético.
- **Bajo una partición de red, elegimos:** consistencia — si la subida a MinIO se corta a mitad de camino, el job de ingesta debe fallar y no dejar el objeto parcial escrito en `cruda`, en vez de continuar y dejar ahí lo que alcanzó a subir.
- **Por qué en este requisito:** todo lo que se construye después —el Parquet de la capa refinada (T6), el análisis histórico (R3), la proyección de almacenamiento (T3)— asume que `cruda` es un snapshot completo y confiable. Un objeto parcial no se distingue de uno completo sin una verificación adicional, así que construir sobre una cruda incompleta produciría resultados silenciosamente equivocados, no un error visible. Es preferible que la ingesta falle esa noche de forma explícita a que corrompa en silencio la base de la que depende el resto del proyecto — el mismo argumento que ya sostiene el equipo en `docs/reto_negocio.md`: SECOP II es dato crítico que no se puede recapturar con la misma fidelidad si se pierde o se corrompe.

---

## Parte C · Defensa ante la gerencia

> **Nota sobre esta sección (ver Supuesto 4).** El proyecto, tal como está construido hoy, no tiene ningún requisito que exija flujo ni casi-real: los tres requisitos reales son lotes. La objeción de la gerencia que sí aplica aquí no es "¿por qué no ponemos todo por lotes en vez de flujo?", sino la versión inversa: **"¿por qué mantener tres cadencias de lote distintas —diaria, mensual y bajo demanda— en vez de un único lote grande que se ejecute una sola vez, que sería aún más barato?"**. La defensa que sigue responde a esa pregunta real.

**El requisito con la exigencia más alta.** Ninguno exige segundos. El más exigente es R2 (ingesta incremental por API), que corre a diario, porque es el único cuyo propósito —mantener el lago sincronizado con lo que el portal ya publicó— pierde sentido si se deja acumular semanas: en ese caso, R2 deja de ser "incremental" y se vuelve una segunda copia de R1.

**El costo de no tenerla.** Si se consolida todo en un solo lote anual, el equipo pierde la capacidad de trabajar sobre datos recientes durante el resto del curso (T3, T6 y los hitos siguientes dependen de poder recalcular sobre un lago que refleje el estado actual del portal, no solo el snapshot inicial de la sesión 1).

**El resto en su propia cadencia.** R1 (ingesta cruda inicial) es un evento que ocurre una vez por extracción completa, no algo que deba repetirse a diario; y R3 (análisis histórico) se ejecuta bajo demanda, cuando el equipo necesita un nuevo agregado, no en un calendario fijo. Forzar los tres a una sola cadencia no ahorra infraestructura —ya son todos lotes, sin colas ni consumidores permanentes— y sí complica el pipeline: unir en un solo job cosas que ocurren por razones distintas (una extracción completa vs. una sincronización incremental vs. un recálculo bajo demanda) mezcla responsabilidades que hoy están separadas y son más fáciles de depurar por separado.

**La conclusión.** Mantener cadencias separadas no cuesta más que un lote único: los tres siguen siendo lotes, sin el gasto de una arquitectura de flujo. Lo que se gana es que cada uno corre cuando su propósito lo exige —R2 a diario porque sincroniza, R1 una vez por extracción porque es un evento raro, R3 bajo demanda porque depende de cuándo se necesita el análisis— sin pagar de más por unificar procesos que no comparten el mismo motivo para ejecutarse.

---

## Autoverificación antes de entregar

- [x] Hay al menos tres requisitos, cada uno con paradigma y una frase de justificación.
- [x] Cada requisito tiene sus dos cifras: frescura exigida y volumen por ciclo, sin celdas vacías.
- [x] La frescura declarada es la exigida por el negocio, no la deseable.
- [x] Se nombra un compromiso CAP concreto, aplicado a un requisito real, con su porqué.
- [~] La defensa sostiene la decisión con qué se rompe sin la frescura crítica, no con la novedad del tiempo real — **adaptada**: no hay requisito de flujo real en el proyecto, así que la Parte C responde a la objeción equivalente que sí aplica (varias cadencias de lote vs. un solo lote). Ver Supuesto 4 y nota al inicio de la Parte C.
- [x] Los supuestos que se tomaron están declarados en la sección 0.
- [ ] **Pendiente por el equipo:** completar carátula (equipo, integrantes, fecha) y **confirmar con el profesor si la Parte C, sin componente de flujo, cumple el criterio de aceptación tal como está reformulada** — es la principal desviación del enunciado literal en esta versión del documento.

---

## Referencias

Brewer, E. A. (2012). CAP twelve years later: How the "rules" have changed. *Computer, 45*(2), 23-29. https://doi.org/10.1109/MC.2012.37

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Reis, J., y Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.

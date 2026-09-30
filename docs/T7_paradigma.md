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
- **Supuesto 2.** Se agrega un cuarto requisito, **R4 · alerta de contratos nuevos con monto atípico o de contratación directa**, consultando la API SODA cada hora. A diferencia de R1-R3 (patrón medido en `docs/T6_formato.md`: escritura rara, lectura frecuente, sin exigencia de frescura menor a días), R4 sí tiene una razón de negocio genuina para exigir horas: una alerta que llega un día después de publicado el contrato ya perdió su valor de detección temprana. **Se declara explícitamente como requisito de diseño, no como algo implementado**: no existe hoy ningún job programado, ninguna regla de umbral codificada ni ningún mecanismo de notificación en el repositorio. El detalle de la arquitectura propuesta para R4 está en `docs/T8_arquitectura.md`, secciones 3 y 4.
- **Supuesto 3.** La ingesta incremental por API SODA (R2) se declara en `ficha_tecnica.md` como mecanismo previsto para las sesiones 12-13, todavía no construido; se documenta aquí como decisión de arquitectura anticipada, no como algo ya en producción.
- **Supuesto 4.** Con R4 incorporado, el proyecto sí tiene un requisito genuino de frescura menor a un día (horas), lo que permite responder la Parte C de forma literal: cuál es el requisito que exige la frescura más alta (R4), qué se rompe si no se le da esa frescura, y por qué conviene un diseño híbrido (varias cadencias de lote, una de ellas horaria) en vez de forzar todo a una sola cadencia diaria o mensual. R4 sigue siendo **casi real por sondeo (polling horario)**, no flujo continuo: no hay justificación de negocio para exigir segundos (una alerta de contratación pública no pierde su valor entre el minuto 1 y el minuto 59 de la misma hora), así que tampoco se fuerza un componente de streaming genuino donde el requisito real solo exige horas.

---

## Parte A · Tabla de asignación de paradigma

| Requisito | Frescura exigida | Volumen por ciclo | Paradigma | Justificación en una frase |
|---|---|---|---|---|
| R1 · Ingesta cruda del dataset completo al lago (capa raw) | Días | ≈ 4,5 GB / ≈ 5,9 M registros por corrida completa | Lotes | Es un snapshot que alimenta el lago; nadie necesita ver el contrato en el segundo en que se publica para esta capa de acumulación |
| R2 · Ingesta incremental por rango de fechas (API SODA) para mantener el lago al día | Días | Cientos de registros por día (≈ 130-155 contratos/día según la muestra) | Lotes | Una corrida diaria alcanza a capturar la publicación real del origen; no hay costo de negocio por un día de rezago en sincronizar el lago |
| R3 · Análisis histórico y agregados de tendencia (por entidad, sector, monto) | Días | Todo el histórico acumulado por corrida (millones de registros), ejecutado punto en el tiempo | Lotes | Un agregado de tendencia no cambia por tener los datos de hoy en vez de los de ayer; el lote es más barato y su lógica es de por sí recalculable sobre todo el histórico |
| R4 · Alerta de contratos nuevos con monto atípico o de contratación directa | Horas | Pocos registros por corrida (≈5-6 contratos/hora en promedio, extrapolado de los ≈130-155 contratos/día observados en la muestra de T1) | Casi real | Una alerta con un día de rezago ya no sirve como detección temprana; pero tampoco hay razón de negocio para exigir segundos, así que un sondeo horario a la API SODA es suficiente |

**Paradigma del proyecto en conjunto:** Híbrido, predominantemente por lotes, con un componente casi real acotado a R4. R1-R3 comparten el patrón ya medido en `docs/T6_formato.md` (escritura rara, lectura frecuente) y no tienen ningún usuario esperando una respuesta en el instante en que el dato se publica. R4 sí tiene esa exigencia, pero acotada a horas, no a segundos: se resuelve con sondeo periódico a la API SODA, no con un componente de streaming continuo (ver Supuesto 2 y Supuesto 4).

---

## Parte B · Compromiso del teorema CAP

- **Requisito sobre el que se decide:** R1 (ingesta cruda del dataset completo al lago). Es el único de los tres con evidencia real de ejecución contra infraestructura de red (MinIO): `docs/T6_formato.md` documenta que el script `src/refinar/convertir_parquet.py` lee de `cruda` vía `s3.download_file`, y `lago-equipo/EVIDENCIA_T5.md` confirma la escritura real al lago. Ahí es donde una partición de red entre el proceso de ingesta y MinIO es un escenario concreto, no hipotético.
- **Bajo una partición de red, elegimos:** consistencia — si la subida a MinIO se corta a mitad de camino, el job de ingesta debe fallar y no dejar el objeto parcial escrito en `cruda`, en vez de continuar y dejar ahí lo que alcanzó a subir.
- **Por qué en este requisito:** todo lo que se construye después —el Parquet de la capa refinada (T6), el análisis histórico (R3), la proyección de almacenamiento (T3)— asume que `cruda` es un snapshot completo y confiable. Un objeto parcial no se distingue de uno completo sin una verificación adicional, así que construir sobre una cruda incompleta produciría resultados silenciosamente equivocados, no un error visible. Es preferible que la ingesta falle esa noche de forma explícita a que corrompa en silencio la base de la que depende el resto del proyecto — el mismo argumento que ya sostiene el equipo en `docs/reto_negocio.md`: SECOP II es dato crítico que no se puede recapturar con la misma fidelidad si se pierde o se corrompe.

---

## Parte C · Defensa ante la gerencia

**El requisito con la exigencia más alta.** R4 (alerta de contratos con monto atípico o de contratación directa), con sondeo horario a la API SODA. Es el único de los cuatro requisitos donde el tiempo entre la publicación del contrato y su detección tiene un costo de negocio directo: un contrato irregular que se detecta un día después ya tuvo un día entero para avanzar sin que nadie lo mirara.

**El costo de no tenerla.** Si R4 se ejecutara con la misma cadencia diaria que R2 en vez de horaria, un contrato publicado a las 8 a.m. con un monto atípico o adjudicado por contratación directa podría no generar alerta hasta la corrida del día siguiente — hasta 24 horas de exposición sin que el equipo (o, en un escenario real, el área de control interno) tenga oportunidad de revisarlo a tiempo. Con sondeo horario, esa ventana baja a menos de 60 minutos en el peor caso.

**Por qué no se lleva a flujo continuo (segundos).** No hay ninguna razón de negocio para exigirlo: un contrato de contratación directa no se vuelve más ni menos irregular entre el segundo 1 y el minuto 59 de la misma hora en que se publicó. Construir un componente de streaming real (broker de eventos, procesamiento continuo) para ganar una ventana de detección de minutos en vez de una hora sería pagar la complejidad operativa de un pipeline de eventos —y el conocimiento nuevo que el equipo tendría que adquirir y mantener— por una mejora que ningún requisito real pide. El sondeo horario es la frontera correcta entre "suficientemente rápido para cumplir su propósito" y "no más caro de lo que el problema exige".

**El resto en su propia cadencia.** R1 (ingesta cruda inicial) es un evento que ocurre una vez por extracción completa; R2 (incremental) corre a diario porque sincroniza el lago con lo ya publicado; R3 (análisis histórico) se ejecuta bajo demanda, cuando el equipo necesita un nuevo agregado. Forzar los cuatro a una sola cadencia no ahorra infraestructura —tres seguirían siendo lotes simples y R4 seguiría necesitando su propia frecuencia para cumplir su propósito— y sí mezcla responsabilidades que hoy están separadas y son más fáciles de depurar por separado.

**La conclusión.** El diseño híbrido —tres cadencias de lote (R1, R2, R3) más un sondeo horario acotado (R4)— cuesta menos que forzar todo a la cadencia más exigente (streaming continuo para todo) y sirve mejor que forzar todo a la cadencia más relajada (un solo lote diario, que dejaría a R4 sin su ventana de detección). Cada requisito corre a la frecuencia mínima que su propósito real exige, ni más ni menos.

---

## Autoverificación antes de entregar

- [x] Hay al menos tres requisitos, cada uno con paradigma y una frase de justificación (ahora cuatro, con R4).
- [x] Cada requisito tiene sus dos cifras: frescura exigida y volumen por ciclo, sin celdas vacías.
- [x] La frescura declarada es la exigida por el negocio, no la deseable.
- [x] Se nombra un compromiso CAP concreto, aplicado a un requisito real, con su porqué.
- [x] La defensa sostiene la decisión con qué se rompe sin la frescura crítica (R4, ver Parte C), no con la novedad del tiempo real.
- [x] Los supuestos que se tomaron están declarados en la sección 0.
- [ ] **Pendiente por el equipo:** completar carátula (equipo, integrantes, fecha); diseñar el mecanismo de notificación de R4 (canal: correo, mensajería u otro — detalle de implementación futura, no bloqueante para T7/T8); y construir R4 cuando el curso llegue a la etapa de implementación (hoy es solo requisito de diseño, ver Supuesto 2).

---

## Referencias

Brewer, E. A. (2012). CAP twelve years later: How the "rules" have changed. *Computer, 45*(2), 23-29. https://doi.org/10.1109/MC.2012.37

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Reis, J., y Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.

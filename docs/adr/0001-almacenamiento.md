# ADR 0001 · Almacenamiento del proyecto: mantener el lago por capas, no adoptar almacén relacional ni lakehouse

**Equipo:** Número 6
**Integrantes:** Ana Sofía Henao Torres, Simón Robles Díaz, Samuel Esteban Gómez Alfonso
**Proyecto:** SECOP II — Contratos Electrónicos
**Fecha:** 2026-09-29
**Curso:** IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean

**Estado:** Aceptado

> Este ADR no elige entre tres opciones en abstracto: ratifica con una matriz explícita una decisión que el proyecto ya venía tomando de hecho desde T5/T6 (construir un lago de tres capas en MinIO), y deja constancia de qué se descartó y por qué, para quien llegue después.

---

## 1. Contexto

El proyecto ya tiene, construido y verificado con ejecución real, un lago de tres capas (`cruda` → `refinada` → `consolidada`) sobre MinIO, con Parquet codec zstd en la capa refinada (T5, T6). También tiene un contenedor PostgreSQL 16 desplegado desde T2, hoy sin poblar. Ningún componente de tipo lakehouse (Delta Lake, Apache Iceberg, Apache Hudi o equivalente) existe hoy en el repositorio.

**Decisión del equipo sobre el rol de PostgreSQL (2026-09-29).** El equipo decidió que PostgreSQL no compite con el lago como almacenamiento principal del dataset — ese papel lo resuelve este mismo ADR a favor del lago (sección 2). PostgreSQL se reserva como **capa de servicio**: guarda resultados ya calculados y listos para consumir, no el dato crudo ni el histórico completo. En concreto, dos usos previstos: los agregados de R3 (análisis histórico y de tendencia, hoy resueltos en la capa `consolidada` en Parquet) y el registro de alertas de R4 (contratos con monto atípico o de contratación directa, ver `docs/T7_paradigma.md`). **Esto es una decisión de diseño, no una implementación**: el contenedor está desplegado desde T2 pero no tiene hoy ningún esquema, ninguna tabla ni ningún job que escriba en él — se declara aquí para que quede registrado el rol previsto, no para dar a entender que ya está poblado.

**La fuerza que obliga a decidir.** T8 ya adoptó la arquitectura "vía única con flujo acotado" (sin capa de velocidad tipo Lambda) apoyada en ese lago de tres capas. Pero T8 no comparó explícitamente almacén, lago y lakehouse con una matriz de criterios — solo asumió el lago porque ya existía desde T5. Este ADR llena ese vacío: compara las tres opciones con una matriz ponderada y registra si la elección de hecho (el lago) resiste el escrutinio explícito, o si debería reconsiderarse.

**Las cifras que alimentan la decisión:**

| Cifra | Valor | Fuente |
|---|---|---|
| Volumen actual estimado (dataset completo) | ≈4,5 GB / ≈5,9 M filas | `docs/ficha_tecnica.md` (T1) |
| Volumen proyectado a 12 meses (V₁₂) | 4,987 GB | `docs/proyeccion_almacenamiento.md` (T3) |
| Reducción de tamaño, CSV → Parquet zstd (muestra sin particionar) | 82 % | `docs/T6_formato.md` |
| Reducción de tamaño, CSV → Parquet zstd (refinada ya particionada) | 74,4 % | `docs/T6_formato.md` |
| Velocidad de consulta selectiva, Parquet vs CSV | ≈87× más rápida | `docs/T6_formato.md` |
| Requisito con mayor exigencia de frescura | R4, horas (sondeo, no streaming) | `docs/T7_paradigma.md` |
| Requisito transaccional o de auditoría genuino hoy | Ninguno (R4 es casi-real por sondeo, no transaccional) | `docs/T7_paradigma.md`, Supuesto 4 |
| Tamaño de equipo | 3 personas, sin presupuesto de infraestructura en la nube | `docs/T8_arquitectura.md`, sección 3 (descarta malla de datos por la misma razón) |

**Coherencia con T7 y T8.** T7 estableció que el proyecto es predominantemente por lotes, con un único componente casi-real (R4) resuelto por sondeo horario, sin ningún requisito genuino de transacciones ACID ni de viaje en el tiempo fila a fila. T8 ya descartó Lambda (sobra para una exigencia de horas) y malla de datos (sobra para un solo dominio y un solo equipo) por el mismo argumento de costo-beneficio que se aplica aquí: no pagar la complejidad de una capacidad que ningún requisito real pide.

---

## 2. Decisión

### 2.1 Matriz de criterios ponderados

Los pesos son el juicio de ingeniería de este equipo, justificado con evidencia del propio proyecto (no con la tabla de referencia genérica de la guía):

| Criterio | Peso | Justificación del peso |
|---|---|---|
| Costo de almacenamiento | 15 % | El volumen proyectado es pequeño (V₁₂ = 4,987 GB, T3); el costo absoluto de cualquier opción es bajo en este rango, así que el criterio pesa menos que en un proyecto de gran escala |
| Flexibilidad de esquema | 15 % | El dataset real tiene 85 columnas frente a las 15 de la muestra de trabajo (T1); el esquema completo aún no se ha verificado, así que la capacidad de ingerir sin migración rígida importa, pero no es el criterio dominante |
| Rendimiento de consulta analítica | 25 % | Es el criterio con evidencia de ejecución real más fuerte del proyecto: R3 (agregados de tendencia) es el uso final del dato, y T6 ya midió el efecto real (Parquet ≈87× más rápido que CSV en la misma consulta) |
| Soporte transaccional y viaje en el tiempo | 10 % | T7 declara explícitamente que ningún requisito del proyecto exige hoy transacciones ACID ni auditoría fila a fila; R4 es casi-real por sondeo, no un flujo transaccional. Peso bajo porque el proyecto no lo necesita, no porque no importe en general |
| Complejidad operativa | 20 % | El equipo son 3 personas sin infraestructura administrada; T8 ya usa este mismo argumento para descartar Lambda y malla de datos. Peso alto porque ya es notable operar tres stacks Docker separados (raíz, `lago-equipo`, `hdfs-cluster-equipo`) |
| Adecuación al volumen y la frescura del proyecto | 15 % | El patrón medido (T6: escritura rara, lectura frecuente) y el paradigma híbrido acotado a horas (T7) ya calzan con un lago de capas simple; el peso es moderado porque este ajuste ya está demostrado en la práctica, no es una incógnita |

**Suma de pesos: 100 %.**

Calificación de 1 (muy débil) a 5 (muy fuerte) de las tres opciones, con la evidencia del propio proyecto entre paréntesis donde existe:

| Criterio | Peso | Almacén (PostgreSQL) | Lago (MinIO + Parquet) | Lakehouse (Delta/Iceberg sobre el mismo lago) |
|---|---|---|---|---|
| Costo de almacenamiento | 15 % | 2 (índices y almacenamiento de fila de PostgreSQL cuestan más por GB que objetos comprimidos) | 5 (Parquet zstd ya midió -74,4 % a -82 % frente a CSV, T6) | 4 (mismo Parquet base, más el costo del log de transacciones y metadatos) |
| Flexibilidad de esquema | 15 % | 2 (requiere migración explícita de esquema; el dataset real de 85 columnas aún no se ha validado contra la muestra de 15) | 5 (schema-on-read; ya absorbió el salto de 15 a 17 columnas en T6 sin migración) | 4 (soporta evolución de esquema, pero con más gobernanza que el lago simple) |
| Rendimiento de consulta analítica | 25 % | 4 (fuerte en teoría para consultas estructuradas, pero sin evidencia de ejecución real en este proyecto: el contenedor está desplegado y sin poblar) | 5 (único con medición real de ejecución: ≈87× más rápido que CSV, T6) | 4 (mismo motor columnar Parquet de base; el valor añadido — indexación y *data skipping* — no se ha probado en este proyecto) |
| Soporte transaccional y viaje en el tiempo | 10 % | 5 (ACID nativo, el punto fuerte real de un motor relacional) | 1 (solo versionado de objeto completo en `cruda` vía S3, no viaje en el tiempo fila a fila, T5) | 5 (ACID y viaje en el tiempo fila a fila son la razón de ser del formato lakehouse) |
| Complejidad operativa | 20 % | 4 (ya desplegado y conocido por el equipo desde T2, sin piezas nuevas que operar) | 3 (ya en operación, pero T8 documenta que ya son tres stacks Docker separados) | 2 (suma un metastore y un motor de log de transacciones sobre la infraestructura que ya cuesta operar) |
| Adecuación al volumen y la frescura del proyecto | 15 % | 2 (un almacén relacional no es el punto de entrada natural para un snapshot CSV crudo de varios GB; obligaría a rediseñar la capa `cruda`) | 5 (es exactamente el patrón ya construido y medido: lotes con lectura frecuente, R4 acotado a horas por sondeo) | 3 (serviría igual de bien técnicamente, pero no hay un requisito real —transaccional o de frescura— que lo justifique hoy) |

### 2.2 Puntajes

$$ \text{puntaje} = \sum_{i=1}^{6} \left( \text{peso}_i \times \text{calificación}_i \right) $$

| Opción | Cálculo | Puntaje |
|---|---|---|
| Almacén (PostgreSQL) | 0,15·2 + 0,15·2 + 0,25·4 + 0,10·5 + 0,20·4 + 0,15·2 | **3,20** |
| Lago (MinIO + Parquet) | 0,15·5 + 0,15·5 + 0,25·5 + 0,10·1 + 0,20·3 + 0,15·5 | **4,20** |
| Lakehouse | 0,15·4 + 0,15·4 + 0,25·4 + 0,10·5 + 0,20·2 + 0,15·3 | **3,55** |

### 2.3 Lectura de ingeniería, no solo del número

El lago gana con un margen amplio: 4,20 frente a 3,55 del lakehouse y 3,20 del almacén — una diferencia de 0,65, no los 0,15 ajustados del ejemplo del acueducto. El puntaje coincide aquí con lo que el proyecto ya construyó desde T5/T6, y por una razón concreta: el criterio de mayor peso (rendimiento de consulta analítica, 25 %) y el de adecuación al volumen y frescura (15 %) ya tienen evidencia de ejecución real a favor del lago, mientras que el único criterio donde el lago es débil (soporte transaccional, calificación 1) pesa apenas 10 % porque ningún requisito del proyecto lo exige hoy (T7).

**Decisión: mantener el lago por capas (MinIO + Parquet zstd) como almacenamiento del proyecto.** No se adopta lakehouse ni se migra a almacén relacional como capa principal en esta etapa. PostgreSQL se reserva como capa de servicio complementaria —no como alternativa al lago— para los resultados ya calculados de R3 y el registro de alertas de R4 (ver sección 1, decisión del equipo sobre su rol); esto no reabre la comparación de la matriz, porque no compite por el rol de almacenamiento principal que la matriz sí evaluó.

---

## 3. Análisis de sensibilidad · Nivel Frontera

El criterio que más generó duda en el equipo fue **soporte transaccional y viaje en el tiempo**: es donde el lago obtiene su calificación más baja (1) y el lakehouse la más alta (5), la mayor brecha de toda la matriz.

**Pregunta:** ¿a partir de qué peso de ese criterio el lakehouse superaría al lago, si el resto de los pesos se reescala proporcionalmente para seguir sumando 100?

Con los pesos originales, la diferencia ponderada por soporte transaccional es (0,10 × 5) − (0,10 × 1) = 0,40 a favor del lakehouse; los otros cinco criterios suman −1,05 a favor del lago (con los pesos originales). Igualando el puntaje total de ambas opciones y resolviendo para el peso *t* de soporte transaccional (reescalando los otros cinco pesos proporcionalmente a partir de 90 %):

$$ t \approx 22,6\,\% $$

Es decir, el peso de soporte transaccional tendría que **más que duplicarse**, de 10 % a cerca de 23 %, para que el lakehouse ganara — y eso sin mover ningún otro peso en su contra, solo cediéndoles espacio proporcionalmente.

**Conclusión de robustez.** La decisión es **robusta**, no sensible: no cambia con un ajuste razonable de pesos. Solo se revertiría si el proyecto adquiriera un requisito genuino y grande de auditoría transaccional — muy por encima de lo que R4 (alerta casi-real por sondeo, sin exigencia ACID, T7) representa hoy. Esto también funciona como umbral de reapertura explícito: si en el futuro aparece un requisito real que justifique subir ese peso a ese orden de magnitud, esta decisión debe revisarse (ver sección 4).

---

## 4. Consecuencias

> Escrita pensando en quien se una al equipo dentro de seis meses y solo tenga este documento para entender por qué el proyecto almacena como almacena.

**Lo que se ganó con esta decisión.** El proyecto sigue apoyado en el lago de tres capas que ya existía desde T5: `cruda` (inmutable, versionada por objeto), `refinada` (Parquet zstd, -74,4 % de tamaño frente a CSV) y `consolidada` (reservada para agregados). Eso da almacenamiento barato a este volumen (T3: V₁₂ = 4,987 GB proyectados a 12 meses), consultas analíticas ≈87 veces más rápidas que sobre CSV (T6) y libertad para ingerir el dataset completo de SECOP II (85 columnas) sin rediseñar el esquema cuando la muestra de 15 columnas deje de ser representativa. No hubo que migrar nada ni introducir un componente nuevo: la decisión ratifica infraestructura ya construida y verificada.

**Lo que se sacrificó, y por qué fue una renuncia razonable.** El proyecto **no tiene transacciones ACID ni viaje en el tiempo fila a fila**. El único mecanismo de recuperación histórica es el versionado de objeto completo de S3 en `cruda` (T5): se puede recuperar el CSV completo de una carga anterior por su `VersionId`, pero no se puede "ver el estado de una fila específica en una fecha pasada" como sí lo daría un formato lakehouse. Se aceptó esa renuncia porque, hoy, ningún requisito del proyecto la necesita: R1-R3 son lotes sin exigencia transaccional (T7), y R4 —el único requisito con frescura de horas— es un sondeo periódico, no una escritura concurrente que necesite aislamiento ACID. Pagar la complejidad operativa de un metastore y un log de transacciones (lakehouse) hoy sería replicar el mismo argumento que T8 ya usó para descartar Lambda: comprar una capacidad que ningún requisito real pide.

**El costo operativo que se acepta mantener.** El equipo sigue operando tres stacks Docker separados (raíz, `lago-equipo`, `hdfs-cluster-equipo`, documentado en T8 sección 4) en vez de uno solo. Esta decisión no lo resuelve ni lo empeora: es una observación de T8, no una consecuencia nueva de T9.

**El contenedor PostgreSQL ya tiene un rol decidido, pero todavía no construido.** El equipo decidió usarlo como capa de servicio para los agregados de R3 y el registro de alertas de R4 — no como almacenamiento principal, ese papel sigue siendo del lago. Hoy sigue desplegado y sin poblar: no hay esquema, tabla ni job que escriba en él. Quien llegue después no debe interpretar el contenedor corriendo como evidencia de que ya sirve agregados — es diseño declarado, igual que R4 lo es en T7/T8, y construirlo es trabajo futuro, no algo que este ADR ya resolvió.

**Cuándo reabrir esta decisión.** Revisar esta decisión si aparece cualquiera de estas señales, no antes:
1. Un requisito real (no hipotético) de auditoría que exija reconstruir el estado exacto de un contrato individual en una fecha pasada — más allá de recuperar el snapshot completo por `VersionId`.
2. R4 deja de ser un sondeo de solo-lectura y pasa a requerir escrituras concurrentes con garantías de aislamiento (por ejemplo, varios procesos actualizando el mismo registro de alerta a la vez).
3. El volumen proyectado crece muy por encima de lo calculado en T3 (V₁₂ = 4,987 GB), al punto de que la indexación y el *data skipping* de un lakehouse dejen de ser opcionales para mantener el rendimiento de consulta.

Si ninguna de estas tres condiciones se cumple, el lago por capas actual sigue siendo la opción correcta, y no hay que revisitar esta decisión solo porque "lakehouse" suene más moderno — esa es precisamente la trampa que la guía de esta sesión advierte evitar.

---

## Autoverificación antes de entregar

- [x] Los seis pesos suman 100, cada uno con una frase de justificación basada en evidencia del propio proyecto (no en la tabla genérica de la guía).
- [x] Las tres opciones están calificadas de 1 a 5 en los seis criterios, sin celdas vacías.
- [x] El ADR es un archivo Markdown versionado en el repositorio (`docs/adr/0001-almacenamiento.md`).
- [x] La matriz ponderada aparece dentro del ADR, no como anexo suelto.
- [x] La decisión es coherente con T7 (paradigma híbrido, R4 casi-real por sondeo) y T8 (arquitectura vía única con flujo acotado, ya apoyada en el lago).
- [x] Las consecuencias incluyen al menos un costo aceptado (ausencia de ACID y viaje en el tiempo fila a fila), no solo ventajas.
- [x] Se identificó el peso que hace bascular la decisión (soporte transaccional) y el umbral donde cambiaría (≈22,6 %), sin forzar los pesos para llegar a un resultado predeterminado.
- [x] El equipo revisó y confirmó los seis pesos y sus justificaciones como su propio juicio de ingeniería (confirmado 2026-09-29), no solo como un borrador de IA sin revisar.
- [x] El equipo decidió el rol de PostgreSQL (capa de servicio para agregados de R3 y registro de alertas de R4, confirmado 2026-09-29) y se declaró explícitamente como diseño, no como implementación.
- [ ] **Pendiente por el equipo:** construir el esquema de PostgreSQL y el job que lo puebla, cuando el curso llegue a la etapa de implementación de R3/R4 (hoy no hay ni esquema ni job, ver sección 4).

---

## Referencias

Armbrust, M., Ghodsi, A., Xin, R., y Zaharia, M. (2021). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. *Proceedings of the 11th Conference on Innovative Data Systems Research (CIDR)*.

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Nygard, M. (2011). *Documenting architecture decisions* [Entrada de blog]. Cognitect.

Reis, J., y Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.

---

## Declaración de uso de IA generativa

- **Herramienta usada:** Claude (Anthropic), a través de Claude Code.
- **En qué parte:** lectura y consolidación de las cifras ya documentadas en T1, T3, T5, T6, T7 y T8; diseño y justificación de los seis pesos de la matriz a partir de esas cifras (no de la tabla de ejemplo genérica de la guía); cálculo de los puntajes y del análisis de sensibilidad (umbral ≈22,6 % para el peso de soporte transaccional); y redacción completa de este documento, incluida la sección de consecuencias para el reto de comunicación.
- **Qué verifiqué:** que cada cifra citada (V₁₂ = 4,987 GB, reducción de 74,4 %/82 %, ≈87× de velocidad de consulta, la ausencia de viaje en el tiempo fila a fila en `cruda`) existe tal cual en el documento fuente indicado entre paréntesis — ninguna se recalculó ni se inventó. El cálculo del umbral de sensibilidad se verificó de dos formas independientes (fórmula algebraica y sustitución numérica directa en la matriz), y ambas coinciden en ≈22,6 %.
- **Verificado por el equipo:** los seis pesos fueron revisados y confirmados por el equipo como su propio juicio de ingeniería (2026-09-29), no aceptados sin revisión.
- **Actualización posterior (2026-09-29):** a petición del equipo, se incorporó la decisión sobre el rol de PostgreSQL (capa de servicio para agregados de R3 y registro de alertas de R4, no almacenamiento principal) en las secciones 1, 2 y 4, y se actualizó `docs/T8_arquitectura.md` (diagrama de contenedor y su descripción) para que ambos documentos queden coherentes. Se declaró explícitamente como diseño no implementado, siguiendo el mismo criterio ya usado para R4 en T7/T8: el contenedor existe desplegado, pero sin esquema ni job que lo pueble.

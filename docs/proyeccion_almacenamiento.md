# T3 · Proyección de almacenamiento y factor de réplica

**Equipo:** [Equipo N0 6]
**Integrantes:** Ana Sofía Henao Torres, [Simón Robles], [Samuel Gomez]
**Fuente consolidada:** SECOP II — Contratos Electrónicos (Colombia Compra Eficiente)

---

## 1. Datos de entrada (de la ficha T1 de Ana Sofía, fuente consolidada del equipo)

| Dato | Valor | Origen |
|---|---|---|
| S₀ · volumen actual (dataset completo, estimado) | 4,500 GB | Escalado proporcional por número de filas (44.400 filas de muestra → 5.900.000 filas del dataset completo reportado en datos.gov.co). Cota inferior: la muestra tiene 15 columnas, el dataset real tiene 85 |
| g · tasa de crecimiento mensual | 0,86 % | Medida sobre la propia fuente: conteo de contratos por mes (`fecha_firma`) dentro de la muestra, comparando el primer y último mes completos disponibles (feb-2024 a sep-2024, 7 períodos) |
| Horizonte de proyección | 12 meses | Pedido por el enunciado de T3 |
| Tamaño de bloque | 128 MB | Valor real de HDFS (no el valor didáctico usado en la sesión de clase) |

## 2. Cálculo: volumen proyectado a 12 meses

$$V_{12} = S_0 \cdot (1+g)^{12}$$

```
V_12 = 4,500 GB × (1 + 0,0086)^12
     = 4,500 GB × 1,1082
     = 4,987 GB
```

**Volumen proyectado a 12 meses: 4,987 GB** (crecimiento de 10,82 % en el año)

## 3. Tabla de proyección — tres factores de réplica

| Factor R | Fórmula | Almacenamiento físico | N.º de bloques (128 MB c/u) | Copias de bloque totales | Nodos que puede perder | Costo relativo |
|---|---|---|---|---|---|---|
| 1 | V₁₂ × 1 | 4,987 GB | 40 | 40 | 0 (sin tolerancia) | 1x |
| 2 | V₁₂ × 2 | 9,974 GB | 40 | 80 | 1 | 2x |
| **3** | V₁₂ × 3 | **14,961 GB** | 40 | **120** | **2** | 3x |

**Cálculo del número de bloques:**
```
N_bloques = ceil(V_12_en_MB / tamaño_bloque_MB)
          = ceil(4.987 GB × 1024 / 128 MB)
          = ceil(5.106,7 MB / 128 MB)
          = ceil(39,9)
          = 40 bloques
```

## 4. Recomendación: Factor de réplica 3

### El argumento (resiliencia frente a costo, no preferencia)

**SECOP II es dato crítico que no se puede recapturar de forma inmediata.** El histórico de contratación pública documenta procesos legales y financieros ya cerrados; si se pierde, no existe una fuente alterna equivalente para reconstruirlo con la misma fidelidad y trazabilidad temporal. Esto lo distingue de dato regenerable (por ejemplo, una caché de resultados intermedios de un cálculo), donde perder una copia solo cuesta tiempo de recómputo, no información.

**El costo absoluto es bajo.** Pasar de factor 2 a factor 3 cuesta 4,987 GB adicionales a los 12 meses — una cifra irrisoria frente a la capacidad de un clúster real, incluso pequeño. La ganancia (tolerar 2 nodos caídos simultáneamente, en vez de 1) es proporcionalmente mucho mayor que el costo marginal.

**Cuándo NO elegiríamos factor 3:** si la fuente fuera de bajo valor informativo, de fácil regeneración, o si el volumen proyectado fuera mucho mayor (cientos de TB), donde el costo de la tercera copia sí se vuelve una decisión financiera relevante y valdría la pena explorar códigos de borrado (erasure coding) como alternativa más económica a la triple copia completa — mencionado en la guía de la sesión como salida fuera del alcance de hoy, pero pertinente para cuando el volumen crezca mucho más.

---

## 5. Evidencia de la lectura en inglés

### Párrafo de síntesis (Kleppmann, 2017 — extracto sobre replicación)

Replication solves the problem of keeping data available and durable when
individual machines fail, by storing the same data on multiple nodes so that
losing one node does not lose the data itself. The trade-off it introduces is
consistency: when data changes, the replicas must be updated, and depending
on the replication method, different replicas may briefly show different
values before converging. Systems must therefore choose how many copies to
keep and how strictly those copies must agree before a write is considered
successful, trading fault tolerance and read availability against write
latency and the complexity of resolving conflicting updates.

*(≈95 palabras)*

### Tres términos nuevos al glosario bilingüe del equipo

| Español | Inglés | Precisión de uso |
|---|---|---|
| Nodo caído / fallo de nodo | node failure | El evento que la réplica está diseñada a tolerar, distinto de una corrupción de dato |
| Escritura / operación de escritura | write | La operación que debe propagarse a las réplicas; el punto donde aparece el compromiso entre consistencia y disponibilidad |
| Divergencia de réplicas | replica divergence | Cuando dos copias del mismo dato muestran valores distintos temporalmente, antes de converger |

---

## 5.5. Nivel 3 — Decisión de tamaño de bloque (evidencia práctica propia)

Además del factor de réplica, HDFS exige decidir el tamaño de bloque. Se probaron
dos configuraciones reales en un clúster HDFS local (1 namenode + 3 datanodes,
Docker Compose), cargando una muestra real de 36,4 MB de SECOP II en cada una:

| Configuración | Tamaño de bloque | Factor R | Bloques generados (muestra 36,4 MB) | Verificado con |
|---|---|---|---|---|
| Nivel 1 (default HDFS) | 128 MB | 3 | 1 bloque | `hdfs fsck -files -blocks -locations` |
| Nivel 2 (experimento) | 8 MB | 2 | 5 bloques | `hdfs fsck -files -blocks -locations` |

**Hallazgo clave:** el tamaño de bloque no afecta cuánto disco físico se ocupa —
eso lo determina únicamente el factor de réplica. Lo que sí afecta es **cuántos
bloques debe rastrear el namenode**, el componente que la propia guía de la sesión
identifica como el punto sensible de la arquitectura (*"el nodo maestro concentra
el conocimiento... por eso se protege con mecanismos de alta disponibilidad"*).

Extrapolando esta relación al **volumen real proyectado a 12 meses** (V₁₂ = 4,987
GB, calculado en la sección 2):

| Tamaño de bloque | N.º de bloques sobre V₁₂ | Copias de bloque (R=3) |
|---|---|---|
| 128 MB | **40** | 120 |
| 8 MB | **639** | 1.917 |

Con bloques de 8 MB, el namenode tendría que rastrear **16 veces más fragmentos**
que con el tamaño estándar de 128 MB, sin ninguna ganancia de espacio a cambio.

### Recomendación de tamaño de bloque: 128 MB (el estándar real de HDFS)

La advertencia de la guía sobre bloques grandes ("desperdician espacio con
archivos pequeños") no aplica a esta fuente: SECOP II es un flujo tabular
continuo de varios GB, no un conjunto de archivos diminutos. Un bloque de 128 MB
no desperdicia nada aquí, y sí reduce drásticamente la carga de metadata sobre el
componente más frágil del clúster.

**Decisión final del equipo para T3: factor de réplica 3, tamaño de bloque 128 MB.**



Con únicamente esta ficha (S₀, g, tamaño de bloque, y las fórmulas de la sección 2-3),
otra persona puede recalcular V₁₂ = 4,987 GB, y de ahí las tres filas de la tabla de
factor de réplica, sin preguntar nada adicional.

## 7. Declaración de uso de IA generativa

- **Herramienta usada:** Claude (Anthropic)
- **En qué parte:** cálculo de la proyección a 12 meses y la tabla de factores de
  réplica, redacción del argumento de recomendación, y borrador del párrafo en inglés
- **Qué verificó el equipo:** [completar — cada integrante debe confirmar que corrió
  el cálculo de forma independiente y obtuvo los mismos números antes de aceptar esta
  versión]

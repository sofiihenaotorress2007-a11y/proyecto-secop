# T6 · Formato y compresión de la capa refinada

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean**
Equipo: Número 6 · Integrantes: Ana Sofía Henao Torres, Simón Robles Díaz, Samuel Esteban Gómez Alfonso
Fuente del proyecto: SECOP II — Contratos Electrónicos (Colombia Compra Eficiente, datos.gov.co)

> Instrucciones. Reemplacen cada campo entre `«»`. No borren los encabezados. Este archivo es el informe; el código va en `src/refinar/`. Recuerden: la decisión del codec se sustenta con estos números, no con una tabla orientativa ni con una recomendación externa.

---

## 1. La conversión

**De dónde a dónde**
De: `cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv` (CSV, 44.400 filas, 15 columnas).
A: `refinada/secop/anio=2024/mes={01..10}/part-0.parquet` (Parquet, codec zstd, particionado por `fecha_firma`).

**Confirmación de la regla de la cruda**
El CSV original permanece intacto en la capa cruda: `src/refinar/convertir_parquet.py` solo lee (`s3.download_file`) el objeto de `cruda`, nunca lo sobrescribe ni lo borra. Verificado después de correr el script con `list_object_versions` sobre el cubo `cruda`: la versión activa sigue pesando 36.357.888 bytes, igual que antes de la conversión. El Parquet se escribió únicamente en `refinada`.

---

## 2. Tabla comparativa de los tres codecs

Medida sobre la misma muestra (`secop_sample_periodo2.csv`, 44.400 filas), con la mediana de 3 corridas por métrica. Lectura selectiva sobre las columnas `fecha_firma` y `valor_contrato`.

| Formato | Tamaño | Tiempo de escritura | Tiempo de lectura selectiva |
|---|---|---|---|
| CSV original | 36.357.888 bytes (34,68 MB) | no aplica | no aplica |
| Parquet snappy | 9.041.125 bytes (8,62 MB) | 0,112 s | 0,003 s |
| Parquet gzip | 5.477.798 bytes (5,22 MB) | 2,048 s | 0,003 s |
| Parquet zstd | 6.420.222 bytes (6,12 MB) | 0,138 s | 0,004 s |

**Reducción de tamaño frente al CSV, del codec elegido (zstd)**
82% (de 34,68 MB a 6,12 MB, sobre la muestra sin particionar usada para medir codecs).

Sobre el Parquet final ya particionado y subido a `refinada` (10 archivos, uno por mes de `fecha_firma`), el total pesa 9.302.245 bytes (8,87 MB) frente a los 36.357.888 bytes del CSV: una reducción del 74,4%. Es menor que el 82% de la muestra sin particionar porque cada uno de los 10 archivos carga su propio encabezado y metadatos de Parquet, y porque el dataset final incluye dos columnas adicionales (`anio`, `mes`) usadas solo para particionar.

---

## 3. La consulta selectiva · nivel Extensión

**La consulta usada**
```sql
SELECT departamento, avg(valor_contrato) AS valor_promedio
FROM read_parquet('muestra_zstd.parquet')  -- o read_csv_auto('muestra.csv') para el comparativo
WHERE valor_contrato IS NOT NULL
GROUP BY departamento
```

| Fuente | Tiempo de la consulta |
|---|---|
| Sobre CSV | 0,5568 s |
| Sobre Parquet (zstd) | 0,0064 s |

**Interpretación**
Parquet fue cerca de 87 veces más rápido. La consulta solo necesita dos de las quince columnas del origen (`departamento`, `valor_contrato`). Sobre CSV, DuckDB debe parsear cada fila completa —las quince columnas, incluyendo texto largo como `descripcion_proceso` u `observaciones`— para descartar después trece de ellas. Sobre Parquet, el formato columnar permite leer del disco únicamente los dos column-chunks que la consulta pide; las demás columnas ni se tocan. La ventaja no depende del codec en sí, sino de la orientación por columnas: el codec solo afina cuánto pesa lo que sí se lee. Ambas consultas devuelven el mismo resultado (verificado por comparación fila a fila), así que la diferencia de tiempo no cuesta corrección.

---

## 4. El codec elegido y su justificación

**Codec elegido**
zstd

**Patrón de acceso del dato**
SECOP II llega como un extracto periódico: se escribe una vez por extracción (una vez al mes o cuando el equipo saca un nuevo snapshot del portal) y a partir de ahí se consulta repetidamente por el equipo de análisis —agregaciones por entidad, departamento, modalidad, rango de fechas— sin volver a reescribirse. Es un patrón de escritura rara, lectura frecuente, y las consultas típicas leen pocas columnas (`valor_contrato`, `departamento`, `fecha_firma`, `estado_contrato`) de las quince disponibles, nunca la fila completa.

**Por qué este codec, según la tabla y el patrón**
Gzip comprime un poco más (85% vs 82% en la muestra), pero cuesta 2,048 s de escritura contra 0,138 s de zstd: casi 15 veces más lento para ganar solo 3 puntos porcentuales de compresión. Como el dato se escribe con poca frecuencia, ese costo de escritura no se paga muchas veces al mes — pero tampoco hay ninguna razón para pagarlo si zstd da casi el mismo ahorro de espacio a una fracción del tiempo. Snappy escribe apenas un poco más rápido que zstd (0,112 s vs 0,138 s, una diferencia irrelevante en un proceso que corre una vez por extracción), pero comprime notablemente menos (75% vs 82%), y aquí sí importa el espacio porque el dato crece cada mes. En lectura selectiva los tres codecs son indistinguibles (3-4 milisegundos): la ganancia real ya la dio la orientación por columnas de Parquet, no el codec. zstd es el punto donde no se sacrifica casi nada de velocidad de escritura frente a snappy, pero sí se gana casi toda la compresión de gzip: es el codec que mejor sirve a un dato que se escribe poco y se lee mucho, sin pagar el costo de escritura de gzip.

---

## 5. Análisis de costo y beneficio · nivel Frontera

Dirigido a la gerencia, en términos que entienda.

| Dimensión | Resultado |
|---|---|
| Ahorro de espacio | De 34,68 MB (CSV) a 6,12 MB (Parquet zstd) sobre la misma muestra: 82% menos espacio. En el dataset final ya particionado en la refinada, de 34,68 MB a 8,87 MB: 74,4% menos. A escala, cada extracción mensual que hoy ocupa ~35 MB en CSV pasa a ocupar entre 6 y 9 MB en Parquet — el costo de almacenamiento del dato crudo baja en más de dos tercios sin perder ni una fila. |
| Efecto en la velocidad | La consulta típica del equipo de análisis (promedio de valor de contrato por departamento) pasa de 0,557 s sobre CSV a 0,006 s sobre Parquet: cerca de 87 veces más rápida. A medida que el dato crece mes a mes, esta ventaja crece con él, porque Parquet solo lee las columnas que la consulta pide. |
| Costo técnico | Escribir con zstd cuesta 0,138 s en la muestra, apenas 0,026 s más que snappy (el más barato de escribir) y 1.500 veces menos tiempo de CPU que gzip (2,048 s). Como la escritura ocurre una sola vez por extracción —no en cada consulta—, este costo es marginal frente al ahorro de espacio y de tiempo de consulta que se repite en cada análisis posterior. |
| Recomendación | Adoptar Parquet con codec zstd en la capa refinada: recorta el almacenamiento en más de dos tercios y acelera las consultas casi 90 veces, a un costo de CPU en la escritura que es prácticamente el mismo que el codec más rápido disponible. |

---

## 6. Reproducibilidad

**Comandos exactos para reproducir la conversión y las cifras**
```bash
# 1) Con el lago (T5) y el resto del stack arriba
docker compose up -d
cd lago-equipo && docker compose up -d && cd ..
docker compose up -d jupyter

# 2) Si el CSV crudo aun no esta en el lago (ya deberia estarlo desde T5)
docker exec proyecto-secop-jupyter python src/ingesta/cargar_cruda.py \
  --fuente data/raw/secop_sample_periodo2.csv \
  --endpoint http://host.docker.internal:9002

# 3) Tabla comparativa de los tres codecs + comparacion DuckDB (Parquet vs CSV)
docker exec proyecto-secop-jupyter python src/refinar/medir_codecs.py \
  --endpoint http://host.docker.internal:9002

# 4) Conversion real: escribe el Parquet particionado (zstd) en la capa refinada
docker exec proyecto-secop-jupyter python src/refinar/convertir_parquet.py \
  --codec zstd \
  --endpoint http://host.docker.internal:9002
```

Comandos exactos, con salidas reales de esta ejecución, en `docs/T6_ejecucion.md`.

**Declaración**
Confirmamos que otra persona, con un clon limpio del repositorio y estos comandos, reproduce la conversión y obtiene las mismas cifras de la tabla comparativa: los tres codecs se midieron sobre la misma descarga del CSV crudo desde `cruda`, con la mediana de 3 corridas por métrica, y la conversión final se verificó comprobando que el CSV en `cruda` no cambió de tamaño ni de versión activa después de escribir el Parquet en `refinada`.

---

## Declaración de uso de IA generativa

- **Herramienta usada:** Claude (Anthropic)
- **En qué parte:** escritura de `src/refinar/lago_utils.py`,
  `src/refinar/medir_codecs.py` y `src/refinar/convertir_parquet.py`; la
  decisión de particionar la refinada por `fecha_firma` (año/mes) en vez
  de por fecha de extracción como la cruda; y la redacción de este
  documento y de `docs/T6_ejecucion.md`.
- **Qué se verificó ejecutando código real:** los tres codecs se
  midieron corriendo el script contra el CSV real descargado del cubo
  `cruda` (no una muestra simulada), dos veces de forma independiente
  (host y contenedor Jupyter), con la mediana de 3 corridas por métrica.
  La conversión final se corrió de verdad contra MinIO, subiendo 10
  particiones reales al cubo `refinada`, y la inmutabilidad de la cruda
  se confirmó listando las versiones del objeto con
  `list_object_versions` antes y después, no asumida. Detalle completo
  en `docs/T6_ejecucion.md`.

---

## Referencias

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Reis, J., y Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.

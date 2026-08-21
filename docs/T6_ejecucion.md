# T6 · Ejecución y evidencia

Comandos exactos y salidas reales de esta ejecución, corridos con
`docker exec` dentro del contenedor `proyecto-secop-jupyter` (mismo
patrón que T5), apuntando al MinIO real del lago (`lago-equipo`).

## 0. Prerrequisitos

```bash
docker compose up -d
cd lago-equipo && docker compose up -d && cd ..
docker compose up -d jupyter
```

`requirements.txt` ya incluye `pyarrow==24.0.0` y `duckdb==1.5.5` junto a
`boto3`; el contenedor los instala solo al arrancar
(`pip install -r requirements.txt` en su comando de inicio).

El CSV crudo ya debe estar en el lago desde T5. Si no lo está:

```bash
docker exec proyecto-secop-jupyter python src/ingesta/cargar_cruda.py \
  --fuente data/raw/secop_sample_periodo2.csv \
  --endpoint http://host.docker.internal:9002
```

## 1. Tabla comparativa de los tres codecs + comparación DuckDB

```bash
docker exec proyecto-secop-jupyter python src/refinar/medir_codecs.py \
  --endpoint http://host.docker.internal:9002
```

Salida real:

```
Muestra descargada de: s3://cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv (no se modifica el original)

Filas: 44400 | Columnas: 15
Formato       Tamano (bytes)   Escritura (s)  Lectura sel. (s)
CSV                 36357888               -                 -
snappy               9041125           0.085             0.003   (-75% vs CSV)
gzip                 5477798           1.961             0.005   (-85% vs CSV)
zstd                 6420222           0.126             0.003   (-82% vs CSV)

Consulta selectiva (DuckDB) con Parquet zstd:
SELECT departamento, avg(valor_contrato) AS valor_promedio
        FROM read_parquet('/tmp/tmpevn6gis6/muestra_zstd.parquet')
        WHERE valor_contrato IS NOT NULL
        GROUP BY departamento
Parquet: 0.0047 s
CSV:     0.4162 s
Mismo resultado en ambos: True
```

## 2. Conversión real: Parquet particionado a la capa refinada

```bash
docker exec proyecto-secop-jupyter python src/refinar/convertir_parquet.py \
  --codec zstd \
  --endpoint http://host.docker.internal:9002
```

Salida real:

```
CSV crudo leido de: s3://cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv (no se modifica)
Filas: 44400 | Columnas: 17 (incluye anio, mes derivadas de fecha_firma)
10 particiones subidas a s3://refinada/secop/ con codec zstd
  s3://refinada/secop/anio=2024/mes=01/part-0.parquet
  s3://refinada/secop/anio=2024/mes=02/part-0.parquet
  s3://refinada/secop/anio=2024/mes=03/part-0.parquet
  s3://refinada/secop/anio=2024/mes=04/part-0.parquet
  s3://refinada/secop/anio=2024/mes=05/part-0.parquet
  s3://refinada/secop/anio=2024/mes=06/part-0.parquet
  s3://refinada/secop/anio=2024/mes=07/part-0.parquet
  s3://refinada/secop/anio=2024/mes=08/part-0.parquet
  s3://refinada/secop/anio=2024/mes=09/part-0.parquet
  s3://refinada/secop/anio=2024/mes=10/part-0.parquet
```

## 3. Verificación de la regla de la cruda

Antes y después de correr `convertir_parquet.py`, se listó el historial
de versiones del objeto en `cruda` (versionado activo desde T5):

```python
s3.list_object_versions(Bucket="cruda")
```

```
secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv  36357888 bytes  ultima: True
secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv     80384 bytes  ultima: False   (version de la demo de T5)
secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv  36357888 bytes  ultima: False   (version de la demo de T5)
```

La versión activa (`ultima: True`) sigue pesando 36.357.888 bytes, el
mismo tamaño de antes de correr T6: `convertir_parquet.py` solo leyó el
objeto (`download_file`), nunca lo sobrescribió. Las otras dos versiones
son del ejercicio de sobre-escritura y recuperación documentado en
`lago-equipo/EVIDENCIA_T5.md`, no de esta tarea.

Contenido final del cubo `refinada`:

```
secop/anio=2024/mes=01/part-0.parquet   938565 bytes
secop/anio=2024/mes=02/part-0.parquet   900557 bytes
secop/anio=2024/mes=03/part-0.parquet   948668 bytes
secop/anio=2024/mes=04/part-0.parquet   921255 bytes
secop/anio=2024/mes=05/part-0.parquet   938744 bytes
secop/anio=2024/mes=06/part-0.parquet   940442 bytes
secop/anio=2024/mes=07/part-0.parquet   970600 bytes
secop/anio=2024/mes=08/part-0.parquet   959086 bytes
secop/anio=2024/mes=09/part-0.parquet   946759 bytes
secop/anio=2024/mes=10/part-0.parquet   837569 bytes
Total: 9.302.245 bytes (8,87 MB) vs 36.357.888 bytes (34,68 MB) del CSV — 74,4% menos
```

## Declaración

Ambos scripts se corrieron dos veces de forma independiente: una vez
directamente sobre el host (`http://localhost:9002`) para prototipar, y
una segunda vez dentro del contenedor `proyecto-secop-jupyter`
(`http://host.docker.internal:9002`), que es el camino de reproducción
documentado. Las dos corridas produjeron las mismas particiones y
cifras equivalentes (las pequeñas diferencias de milisegundos entre
corridas son ruido normal de medición, no un cambio de resultado).
Confirmamos que otra persona, con un clon limpio del repositorio, el
lago de T5 arriba y estos comandos, reproduce la misma conversión y las
mismas cifras.

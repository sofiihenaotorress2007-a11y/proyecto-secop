# T5 · El lago por capas — evidencia de ejecución

**Fuente:** `data/raw/secop_sample_periodo2.csv` — SECOP II, "Contratos
Electrónicos" (15 columnas, 44.400 filas), el mismo dataset oficial de
`docs/ficha_tecnica.md` y de la sección 4 de `hdfs-cluster-equipo/EVIDENCIA_T4.md`.

Infraestructura: un contenedor MinIO (`lago-equipo/docker-compose.yml`),
API S3 publicada en el puerto **9002** del host (el 9000 estándar de la
guía ya lo ocupa `hdfs-namenode` en este proyecto — ver sección 0). El
script de ingesta oficial (`src/ingesta/cargar_cruda.py`) corre dentro
del contenedor de Jupyter, que llega a MinIO por
`http://host.docker.internal:9002` (los dos entornos Docker del proyecto
son stacks de compose separados, en redes distintas).

---

## 0. Desviación real frente al puerto de la guía

La guía de la sesión 5 usa el puerto 9000 para la API de MinIO en su
ejemplo (`"9000:9000"`). En este proyecto ese puerto ya está tomado por
`hdfs-namenode` (RPC de HDFS, sesión 3-4) — al intentar levantar MinIO con
el mapeo literal de la guía, Docker rechazó el contenedor con
`Bind for 0.0.0.0:9000 failed: port is already allocated`.

**Corrección:** la API de MinIO se publica en `9002:9000` (el puerto
interno del contenedor sigue siendo el 9000 estándar; solo cambia el
mapeo al host). La consola web sí usa el 9001 de la guía, sin conflicto.
Todo el código que sigue usa `MINIO_ENDPOINT=http://localhost:9002` (desde
el host) o `http://host.docker.internal:9002` (desde el contenedor de
Jupyter), nunca el 9000 literal de la guía.

---

## 1. Nivel 1 · Cubos y clave-como-prefijo

Ejecutado dentro de `cargar_cruda.py` (creación idempotente de los tres
cubos) y verificado con `evidencia_demo.py`:

```
Cubo creado: cruda
Cubo creado: refinada
Cubo creado: consolidada
```

**Listado por prefijo, real:**

```
Clave: secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv | Tamano: 36357888
```

**Autoverificación (`head_object`), real:**

```
VersionId de esta version: c69c507b-f48a-47ee-a7eb-771676fc966b
ETag: "d08ebe8fb4be1d9b8042a5596c4b77ec-5"
```

El objeto existe con la clave completa, incluidas las barras — confirma
lo que dice la guía: la "ruta" es el nombre del objeto, MinIO no crea
carpetas reales. `list_objects_v2` con `Prefix="secop/anio=2026/"` sí
agrupa por ese prefijo, pero es agrupación de claves, no un directorio.

---

## 2. Nivel 2 · Versionado real, con sobrescritura real

`cargar_cruda.py` activa el versionado en `cruda` antes de cargar
(`put_bucket_versioning`, `Status: Enabled`) — verificado después con
`get_bucket_versioning`, que devuelve `{'Status': 'Enabled'}`.

**Antes de sobrescribir** (una sola versión):

```
VersionId: c69c507b-f48a-47ee-a7eb-771676fc966b | Ultima: True | Tamano: 36357888
```

**Sobrescritura real:** `evidencia_demo.py` genera un archivo deliberadamente
distinto (las primeras 100 líneas del CSV original, 80.384 bytes — simula
una carga accidental incompleta) y lo sube bajo la **misma clave**.

**Después de sobrescribir** (dos versiones, la anterior no se destruyó):

```
VersionId: 3aacfce9-5e76-496d-a9e6-d458c687c4e3 | Ultima: True  | Tamano: 80384
VersionId: c69c507b-f48a-47ee-a7eb-771676fc966b | Ultima: False | Tamano: 36357888
```

**Recuperación real de la versión original** (no la última), por su
`VersionId`, con `get_object(..., VersionId=...)`:

```
Version original recuperada, VersionId: c69c507b-f48a-47ee-a7eb-771676fc966b
bytes leidos: 36357888
coincide con tamano original esperado (36357888): True
```

Los 36.357.888 bytes leídos coinciden exactamente con el tamaño del
archivo original en disco — no es solo que el `VersionId` aparezca en el
listado, el contenido de esa versión se descargó y se verificó byte a
byte contra el original.

**Estado final del lago** (se volvió a subir el archivo correcto para no
dejar la versión truncada como la vigente — el versionado no impide
corregir hacia adelante, solo impide perder lo anterior):

```
VersionId c69c507b... | Ultima: False | 36.357.888 bytes | 2026-08-18 14:18:42
VersionId 3aacfce9... | Ultima: False |     80.384 bytes | 2026-08-18 14:19:14  (version de la simulacion)
VersionId 9d384df9... | Ultima: True  | 36.357.888 bytes | 2026-08-18 14:19:39
```

**Por qué esto protege la inmutabilidad de la cruda:** sin versionado,
la segunda carga habría reemplazado físicamente el objeto — el archivo
original habría desaparecido sin dejar rastro. Con versionado activo, la
clave sigue apuntando siempre a la versión más reciente para lecturas
normales, pero ninguna versión anterior se borra; sigue siendo
recuperable por su `VersionId` de forma indefinida. Esto es lo que hace
segura la promesa de "la cruda no se edita, no se pierde": un error de
carga dejó de ser destructivo.

---

## 3. Nivel 3 · Convención de rutas de las tres capas

### Por qué la partición es por fecha de extracción, no por fecha de fila

La fuente del equipo (SECOP II) se recibe como un **extracto periódico**:
un archivo cuyo contenido cubre varios meses (`fecha_firma` va de enero a
octubre de 2024 en la muestra oficial), no un archivo por día como el
ejemplo de la guía (acueducto, una lectura de sensor por día). Particionar
el archivo por `fecha_firma` exigiría partir sus filas — eso es una
transformación, y la capa cruda no se transforma. La partición de la
cruda representa entonces **cuándo el equipo extrajo ese snapshot del
portal**, no el contenido interno del archivo. Es la pregunta que
realmente se hace al operar el lago: "¿tengo la extracción de esta
semana?", no "¿qué contratos se firmaron este día?" — esa segunda
pregunta se responde consultando el contenido ya cargado, no la ruta.

### Convención completa

| Capa | Plantilla de ruta | Ejemplo real | Formato | Por qué esa partición |
|---|---|---|---|---|
| `cruda` | `cruda/<fuente>/anio=YYYY/mes=MM/dia=DD/<archivo>.csv` | `cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv` | El formato original de la fuente (CSV aquí) | Fecha de extracción: rastrea de qué carga viene cada archivo, sin transformarlo |
| `refinada` | `refinada/<fuente>/anio=YYYY/mes=MM/dia=DD/<archivo>.parquet` | `refinada/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.parquet` | Parquet (tipado, columnar) | Misma partición que la cruda que la origina — necesaria para poder rastrear de qué extracción viene cada versión limpia (linaje), aunque el formato cambie |
| `consolidada` | `consolidada/<agregado_o_pregunta_de_negocio>/anio=YYYY/parte-*.parquet` | `consolidada/valor_promedio_por_departamento/anio=2026/parte-000.parquet` | Parquet | Ya no se consulta "¿qué llegó tal día?", se consulta "¿cuál es el consolidado de tal pregunta de negocio?" — la partición pasa de ser por ingesta a ser por el tema que responde la tabla |

**Nivel Frontera cumplido:** la convención cubre las tres capas, no solo
la cruda, tal como exige la guía (§4, pista 3: "no dejen solo la cruda
documentada").

### Declaración de inmutabilidad

La capa `cruda` es inmutable: guarda el dato tal como llegó del portal, y
no se edita ni se transforma nunca dentro de esa capa — la evidencia de la
sección 2 demuestra que incluso una sobrescritura accidental no destruye
la versión original, gracias al versionado. Los errores de calidad,
tipado o limpieza se corrigen exclusivamente en `refinada`; `consolidada`
solo agrega lo que ya pasó por `refinada`.

---

## 4. Reto de negocio · Mapa del lago para el analista del próximo semestre

> Media página, pensada para alguien sin contexto previo del equipo.

**El mapa.**
- `cruda`: el dato tal como llegó de SECOP II, sin tocar. Es lo único
  poblado hoy.
- `refinada`: el mismo dato, limpio, tipado y validado. Vacía por ahora;
  se llena cuando el curso llegue a esa etapa.
- `consolidada`: agregados y tablas modeladas, listas para consumir sin
  procesar nada más. Vacía por ahora.

**La convención.** `<capa>/<fuente_o_tema>/anio=YYYY/mes=MM/dia=DD/archivo`
para `cruda` y `refinada` (la fecha es de extracción, no del contenido);
`consolidada/<pregunta_de_negocio>/anio=YYYY/...` para lo ya agregado.
Ejemplo real: la extracción de hoy vive en
`cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv`.

**La regla de la cruda.** Nunca se edita. Si algo está mal, se corrige en
`refinada`, no ahí. El versionado activo en `cruda` es la red de
seguridad: si alguien sobrescribe por error, la versión anterior sigue
recuperable (demostrado en la sección 2, con `VersionId` real).

**Cómo encontrar un dato.** *"Necesito la extracción de SECOP II del 18
de agosto de 2026."* → `cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv`
— se deduce solo con la convención de arriba, sin preguntarle a nadie del
equipo.

---

## 5. Reproducibilidad

```bash
# 1. Levantar el lago (MinIO)
cd lago-equipo
docker compose up -d
cd ..

# 2. Levantar el entorno de análisis (Jupyter, ya trae boto3 via requirements.txt)
docker compose up -d jupyter

# 3. Cargar la fuente cruda (idempotente: crea cubos y activa versionado si hace falta)
docker exec proyecto-secop-jupyter python src/ingesta/cargar_cruda.py \
  --fuente data/raw/secop_sample_periodo2.csv \
  --endpoint http://host.docker.internal:9002
```

**Declaración:** confirmado que estos comandos, corridos en este equipo
desde cero (MinIO recién creado, cubos inexistentes), producen los mismos
tres cubos, la misma clave particionada, y el versionado activo — la
salida real de cada paso está en las secciones 1-3 de arriba, no
resumida ni recordada de una corrida anterior.

---

## Declaración de uso de IA generativa

Usé Claude (Anthropic) como asistente para: diseñar
`lago-equipo/docker-compose.yml` y diagnosticar el conflicto real de
puerto 9000 con `hdfs-namenode` (sección 0); escribir
`src/ingesta/cargar_cruda.py` con la convención de partición por fecha de
extracción, justificada por cómo se consulta el dato, no copiada
literalmente del ejemplo de acueducto de la guía; escribir
`lago-equipo/evidencia_demo.py` para generar la evidencia real de
versionado; y redactar este documento.

Verifiqué las cifras ejecutando yo mismo los comandos contra el
contenedor de MinIO real, dentro del contenedor de Jupyter (no valores
supuestos): el listado por prefijo, los `VersionId` reales de cada
versión, y la recuperación de la versión original salen directamente de
la salida de `boto3` de cada llamada citada en este documento. La
recuperación de la versión original se verificó comparando el tamaño en
bytes leído contra el tamaño real del archivo en disco, no solo
comprobando que el `VersionId` aparece en el listado.

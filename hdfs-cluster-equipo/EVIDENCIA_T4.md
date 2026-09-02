# T4 · MapReduce, contadores de mezcla y combinador — evidencia de ejecución

**Fuente:** `secop_sample.csv` — SECOP II, dataset "Procesos de Contratación"
(59 columnas, 200.000 filas). Distinto del dataset "Contratos Electrónicos"
(jbjy-vk9h) documentado en `docs/ficha_tecnica.md` del repo `proyecto-secop`;
se usó este por ser el único CSV de SECOP II disponible en la máquina al
momento de la práctica.

**Actualización (2026-08-18):** una vez disponible el archivo oficial
(`secop_sample_periodo2.csv`, 15 columnas, el mismo que documenta T1/T3), se
repitieron los Niveles 1-3 sobre él en el mismo clúster real — ver
**sección 4**. Las secciones 1-3 de abajo se dejan intactas como evidencia
real de esa primera ejecución (fue real, solo que sobre el archivo
equivocado); la sección 4 es la que corrige el dataset.

Clúster: 1 namenode + 3 datanodes (HDFS, réplica 3, bloque 128 MB) + 1
resourcemanager + 1 nodemanager + 1 historyserver (YARN), extendido sobre
`hdfs-cluster-equipo/docker-compose.yml` según la guía S04_P4.

---

## 0. Configuración real necesaria (no cubierta por la guía base)

La guía da un `hadoop.env` mínimo para YARN. En la práctica, tres piezas
adicionales fueron necesarias para que un job de Hadoop Streaming corriera,
todas verificadas por fallo real y luego corregidas:

| Problema real observado | Causa | Corrección |
|---|---|---|
| `Could not find or load main class org.apache.hadoop.mapreduce.v2.app.MRAppMaster` | Falta `HADOOP_MAPRED_HOME` en el entorno del ApplicationMaster | Se agregó `YARN_CONF_yarn_app_mapreduce_am_env`, `YARN_CONF_mapreduce_map_env`, `YARN_CONF_mapreduce_reduce_env` = `HADOOP_MAPRED_HOME=/opt/hadoop-3.2.1` en `hadoop.env` |
| `InvalidAuxServiceException: The auxService:mapreduce_shuffle does not exist` | El nodemanager no tenía registrado el servicio auxiliar de shuffle | Se agregó `YARN_CONF_yarn_nodemanager_aux___services=mapreduce_shuffle` y `..._mapreduce_shuffle_class=org.apache.hadoop.mapred.ShuffleHandler` |
| `PipeMapRed.waitOutputThreads(): subprocess failed with code 127` | Las imágenes `bde2020/hadoop-*` (Debian 9 stretch) no traen Python instalado | Se instaló `python3` en el contenedor `nodemanager` (repos de `archive.debian.org`, ya que stretch está EOL en `deb.debian.org`). **Resuelto de forma permanente:** la instalación ahora vive en `hdfs-cluster-equipo/nodemanager/Dockerfile`, y `docker-compose.yml` construye el `nodemanager` desde ahí (`build: ./nodemanager`) en vez de usar la imagen base directa — sobrevive a recrear el contenedor. Pendiente de verificar con un build real (ver nota en "Ausencias y desviaciones") |
| Job corría pero fallaba en el mapper | `mapper.py`/`reducer.py` usaban f-strings (Python 3.6+); el `python3` instalado en el nodemanager es 3.5.3 | Se reescribieron con `.format()` |
| 51.465 líneas físicas de más sobre 200.000 filas lógicas | Campos de texto libre (`nombre_del_procedimiento`, `descripci_n_del_procedimiento`) con saltos de línea dentro de comillas; Hadoop Streaming parte la entrada por línea física | Preprocesamiento con `csv.reader`/`csv.writer` que colapsa saltos de línea internos a espacio, verificado: salida = 200.001 líneas físicas exactas |

Estos cinco hallazgos están documentados aquí porque **son evidencia real de
ejecución**, no supuestos — cada uno rompió un intento real y quedó resuelto
antes de medir nada.

---

## 1. Nivel 1 · Guiado — promedio de `precio_base` por `departamento_entidad`

**Clave:** `departamento_entidad` (columna 2 de 59) · **Valor:** `precio_base`
(columna 20), promedio.

Archivos: `muestra/mapper.py`, `muestra/reducer.py`.

```
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -files /muestra/mapper.py,/muestra/reducer.py \
  -mapper mapper.py -reducer reducer.py \
  -input /entrada/secop_sample_clean.csv -output /salida1
```

**Contadores reales (job `job_1786763862243_0002`):**

| Contador | Valor |
|---|---|
| Map input records | 200.001 |
| Map output records | 200.000 |
| Combine input/output records | 0 (sin combinador) |
| Reduce input groups (departamentos distintos) | 34 |
| **Reduce shuffle bytes** | **5.631.044** |
| Reduce output records | 34 |

`_SUCCESS` verificado. Salida: `part-00000` con 34 líneas, una por
departamento (ej. `Distrito Capital de Bogotá  2317538217.32`).

---

## 2. Nivel 2 · Aplicado — combinador

Requisito: el combinador no promedia, emite suma parcial y conteo; el
reductor final suma las sumas, suma los conteos y solo entonces divide.
Como el combinador puede ejecutarse 0, 1 o varias veces, su entrada y su
salida deben tener el mismo formato (`suma,conteo`) — por eso el mapper de
este nivel (`mapper2.py`) emite `precio_base,1` desde el inicio, en vez de
reusar el `mapper.py` del nivel 1.

Archivos: `muestra/mapper2.py`, `muestra/combiner.py`, `muestra/reducer2.py`.

**Verificación de correctitud antes de ejecutar en el clúster:** se corrió
el pipeline localmente aplicando `combiner.py` dos veces seguidas
(simulando que Hadoop lo invoque más de una vez) y se comparó contra el
resultado del nivel 1 sobre el mismo subconjunto — **idéntico, sin
diferencias**.

**Contadores reales (job `job_1786763862243_0003`):**

| Contador | Sin combinador (Nivel 1) | Con combinador (Nivel 2) |
|---|---|---|
| Map output records | 200.000 | 200.000 |
| Combine input records | 0 | 200.000 |
| Combine output records | 0 | 68 (2 map tasks × 34 departamentos) |
| **Reduce shuffle bytes** | **5.631.044** | **2.194** |
| Reduce output records | 34 | 34 |

**Reducción de bytes de mezcla: 99,96 %** ((5.631.044 − 2.194) / 5.631.044).

**Verificación de correctitud en el clúster:** se descargaron `part-00000`
de `/salida1` y `/salida2` y se compararon línea por línea (`Compare-Object`
en PowerShell) — **idénticos, departamento por departamento**.

---

## 3. Nivel 3 · Autónomo — agregación propia

**Pregunta de negocio:** ¿qué modalidad de contratación concentra más
presupuesto base ofertado en total? (agregación distinta del nivel 1: suma,
no promedio; clave distinta: `modalidad_de_contratacion`, columna 21).

A diferencia del promedio, la suma no necesita cargar un conteo junto al
valor — la suma de sumas parciales sigue siendo la suma total sin importar
cuántas veces corra el combinador. Por eso `mapper3.py` emite el valor
crudo directamente y `combiner3.py`/`reducer3.py` comparten el mismo
formato de entrada y salida.

### Predicción (antes de ejecutar)

- **Sin combinador:** ~200.000 pares cruzan la mezcla, uno por registro de
  entrada (igual orden que el nivel 1).
- **Con combinador:** del orden de (número de map splits) × (claves
  distintas). Un conteo previo sobre la muestra completa mostró **17
  modalidades distintas**; los jobs anteriores mostraron 2 map splits para
  este archivo (`number of splits:2`) → predicción: del orden de 2×17 = 34
  pares.

### Medición real

| Contador | Sin combinador (`job_...0004`) | Con combinador (`job_...0005`) |
|---|---|---|
| Map output records | 200.000 | 200.000 |
| Reduce input groups | 17 | 17 |
| Combine output records | — | 34 |
| **Reduce shuffle bytes** | **8.015.017** | **1.735** |

Predicción confirmada: 200.000 pares sin combinador (coincide exactamente);
34 pares combinados con combinador (coincide exactamente con 2×17).
Reducción de bytes de mezcla: **99,98 %**.

`_SUCCESS` verificado en ambos; resultados comparados con `Compare-Object`
— idénticos.

### Razonamiento de sesgo

Distribución real de `modalidad_de_contratacion` sobre las 200.000 filas:

| Modalidad | Registros | % del total |
|---|---|---|
| Contratación directa | 90.010 | 45,0 % |
| Contratación régimen especial | 77.993 | 39,0 % |
| (resto: 15 modalidades) | 32.997 | 16,0 % |

**Las dos modalidades más frecuentes concentran el 84 % de los registros**,
frente a modalidades como "Concurso de méritos con precalificación" (2
registros) o "Subasta de prueba" (109). Con un solo reductor esto no se
nota, pero si el job se particionara con más de un reductor, la tarea que
reciba `Contratación directa` cargaría casi la mitad del trabajo total
mientras otras terminarían casi de inmediato — el clásico problema de clave
caliente (*hot key*). El combinador reduce el **volumen** de bytes que
cruzan la mezcla, pero no corrige este **desbalance**: sigue habiendo una
clave que domina.

Dato adicional interesante para la nota técnica: el orden por *registros*
no coincide con el orden por *presupuesto total*. "Contratación régimen
especial (con ofertas)" tiene solo 2.989 registros pero el mayor
`precio_base` acumulado (38,48 billones), muy por encima de "Contratación
directa" (90.010 registros, 7,82 billones) — volumen de trámites y volumen
de dinero son cosas distintas.

**Mitigación si el desbalance fuera un problema real:** una clave
compuesta (`modalidad_de_contratacion` + `departamento_entidad`, por
ejemplo) partiría "Contratación directa" en ~34 sub-claves geográficas,
repartiendo la carga entre reductores a costa de un resultado más granular
que habría que reagregar después.

---

## 4. Verificación sobre el dataset oficial (T1/T3) — `secop_sample_periodo2.csv`

Repetición de los Niveles 1-3 sobre `secop_sample_periodo2.csv` (SECOP II,
"Contratos Electrónicos", 15 columnas, 44.400 filas), el mismo archivo que
documentan `docs/ficha_tecnica.md` y `docs/proyeccion_almacenamiento.md`.
Mismo clúster real (namenode + 3 datanodes + YARN) que las secciones 1-3.

**Equivalencia de columnas** (el archivo oficial no tiene `precio_base` ni
`departamento_entidad`; se usaron las columnas más cercanas):

| Sección 1-3 (`secop_sample.csv`, 59 col.) | Sección 4 (`secop_sample_periodo2.csv`, 15 col.) |
|---|---|
| `departamento_entidad` (col. 2) | `departamento` (col. 8) |
| `precio_base` (col. 20) | `valor_contrato` (col. 6) |
| `modalidad_de_contratacion` (col. 21) | `modalidad_contratacion` (col. 3) |

Scripts nuevos en `hdfs-cluster-equipo/muestra_t1t3/` (mismo diseño que
`muestra/`: sin f-strings por Python 3.5.3, `csv.reader` por los campos de
texto libre con comas entre comillas). **No hizo falta preprocesar el CSV**
como en la sección 0: `wc -l` da exactamente 44.401 líneas físicas (44.400
filas + encabezado), sin saltos de línea embebidos en los campos de texto
libre de este archivo.

### Nivel 1 vs. Nivel 2 — promedio de `valor_contrato` por `departamento`

```
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -files /muestra_t1t3/mapper.py,/muestra_t1t3/reducer.py \
  -mapper mapper.py -reducer reducer.py \
  -input /entrada_t1t3/secop_sample_periodo2.csv -output /salida1_t1t3
```

**Contadores reales:**

| Contador | Sin combinador (`job_1787058871039_0001`) | Con combinador (`job_..._0002`) |
|---|---|---|
| Map input records | 44.401 | 44.401 |
| Map output records | 44.400 | 44.400 |
| Combine input/output records | 0 (sin combinador) | 44.400 / 12 (2 map tasks × 6 departamentos) |
| Reduce input groups (departamentos distintos) | 6 | 6 |
| **Reduce shuffle bytes** | **949.538** | **378** |
| Reduce output records | 6 | 6 |

**Reducción de bytes de mezcla: 99,96 %** ((949.538 − 378) / 949.538).

`_SUCCESS` verificado en ambos. `part-00000` de `/salida1_t1t3` y
`/salida2_t1t3` comparados línea por línea (`diff`) — **idénticos**:

```
Boyacá          50232809.29090664
Cauca           48659003.07095554
Cundinamarca    50531423.11127697
Córdoba         50661399.8903132
Nariño          50951358.34227086
Tolima          49981018.00244765
```

**Nota real, no ajustada:** esta muestra de 44.400 filas solo tiene **6
departamentos distintos** (frente a los 34 de la sección 1, que corría sobre
las 200.000 filas del otro archivo) — el archivo oficial de T1/T3 es una
muestra más pequeña y menos diversa geográficamente. No se fuerza a que
coincida con la sección 1; es evidencia real de un archivo distinto.

### Nivel 3 — suma de `valor_contrato` por `modalidad_contratacion`

Misma lógica que la sección 3: `mapper3.py` emite el valor crudo, la suma
de sumas parciales no necesita conteo.

| Contador | Sin combinador (`job_..._0003`) | Con combinador (`job_..._0004`) |
|---|---|---|
| Map output records | 44.400 | 44.400 |
| Reduce input groups | 5 | 5 |
| Combine output records | — | 10 (2 map tasks × 5 modalidades) |
| **Reduce shuffle bytes** | **1.477.568** | **386** |

**Reducción de bytes de mezcla: 99,97 %** ((1.477.568 − 386) / 1.477.568).

`_SUCCESS` verificado en ambos; `part-00000` comparados línea por línea
(`diff`) — **idénticos**:

```
Concurso de méritos     427879788817.0
Contratación directa    448417532608.0
Licitación pública      449304128809.0
Mínima cuantía          453185196752.0
Selección abreviada     448750044047.0
```

**Diferencia real frente a la sección 3 (sesgo de clave):** en este archivo
las 5 modalidades están casi perfectamente balanceadas por número de
registros (8.613 a 8.969 cada una, verificado contando la columna
`modalidad_contratacion` sobre el CSV completo) — a diferencia de la
sección 3, donde dos modalidades concentraban el 84 % de las filas. **En
este dataset no hay problema de clave caliente** para esta clave; es una
observación real, no una limitación oculta del análisis.

### Conclusión de esta sección

Con el dataset oficial de T1/T3, el patrón cualitativo del combinador se
sostiene (reducción de bytes de mezcla >99,9 % en ambos niveles,
resultados idénticos con y sin combinador), pero las cifras absolutas y la
cardinalidad de las claves son distintas a las de las secciones 1-3 — como
era de esperar, al ser un archivo distinto. Esta sección resuelve el
pendiente declarado en "Ausencias y desviaciones": el equipo ya tiene
evidencia real de T4 corrida sobre el dataset que documentan T1 y T3.

---

## 5. Reto de negocio · Nota técnica para gerencia

> **Para:** Gerencia del acueducto (encargo del ejercicio) — agregación por
> departamento rápida y barata.
> **De:** Equipo proyecto-secop.

**La solución.** Job de Hadoop Streaming en Python: `mapper2.py` lee cada
proceso de contratación y emite `departamento_entidad → precio_base,1`;
`combiner.py` agrega localmente en cada nodo de mapa (suma parcial y
conteo, nunca un promedio); `reducer2.py` suma las sumas y los conteos de
todos los nodos y solo entonces divide, produciendo el precio base
promedio por departamento.

**La clave.** `departamento_entidad`: agrupa el 100 % de los registros en
solo 34 valores posibles, lo que da al combinador máximo margen para
comprimir antes de la mezcla — cada nodo de mapa entrega como máximo 34
pares combinados en vez de decenas de miles de pares crudos.

**La evidencia (medida, no supuesta).** Sin combinador, 200.000 pares
cruzan la mezcla: 5.631.044 bytes. Con combinador, el mismo trabajo cruza
la mezcla en 2.194 bytes — **una reducción del 99,96 %**, verificada con
los contadores reales de YARN (`job_1786763862243_0002` vs
`job_1786763862243_0003`, historial en `localhost:8188`). El resultado
numérico es idéntico en ambos casos, comparado línea por línea.

**El riesgo.** La clave sí tiene sesgo: el Distrito Capital de Bogotá
concentra 57.415 de 200.000 registros (28,7 %), muy por encima del segundo
departamento (Antioquia, 21.211, 10,6 %). Con un solo reductor esto no
afecta el tiempo del trabajo, pero si el clúster creciera y se
particionara el trabajo entre varios reductores, el que reciba Bogotá
cargaría casi tres veces más que el promedio de los demás. Si eso se
vuelve un cuello de botella medible, la mitigación es una clave compuesta
(departamento + una segunda dimensión, p. ej. modalidad o mes), a costa de
tener que reagregar el resultado más granular después.

---

## 6. Ausencias y desviaciones (declaradas, no ocultas)

- **Fuente usada vs. fuente documentada en T1/T3 — resuelto (2026-08-18):**
  las secciones 1-3 corrieron sobre `secop_sample.csv` (dataset "Procesos de
  Contratación", 59 columnas, 200.000 filas), no sobre
  `secop_sample_periodo2.csv` (dataset "Contratos Electrónicos", 15
  columnas) que documenta `docs/ficha_tecnica.md`, porque ese archivo no
  estaba disponible en la máquina al momento de la práctica original. Ya se
  consiguió el archivo oficial y se repitieron los Niveles 1-3 sobre él en
  el mismo clúster real, con contadores reales — ver **sección 4**. Se
  conservan las secciones 1-3 tal cual (evidencia real, solo que del
  archivo equivocado) en vez de borrarlas, siguiendo el mismo principio de
  no ocultar lo que pasó de verdad.
- **Instalación de Python en el nodemanager** — resuelto: se movió a
  `hdfs-cluster-equipo/nodemanager/Dockerfile`, que el `docker-compose.yml`
  ahora construye (`build: ./nodemanager`) en vez de usar la imagen base
  `bde2020/hadoop-nodemanager` directamente. **Sin verificar con un build
  real todavía** (Docker Desktop no estaba corriendo al escribir este
  Dockerfile) — antes de confiar en él, alguien del equipo debe correr
  `docker compose up -d --build` y repetir al menos el job del Nivel 1 para
  confirmar que `python3` queda disponible y el job corre igual que antes.
- **Python 3.5.3** es la versión real disponible en el clúster (Debian 9
  stretch, EOL). Todo el código Python de esta práctica evita
  deliberadamente sintaxis de 3.6+ (f-strings) por esta razón.

---

## Declaración de uso de IA generativa

Usé Claude (Anthropic) como asistente para: extender `docker-compose.yml`
y `hadoop.env` con los servicios de YARN de la guía S04_P4; diagnosticar y
corregir tres fallos reales de configuración no cubiertos por la guía
(`HADOOP_MAPRED_HOME`, `mapreduce_shuffle`, Python ausente en las imágenes
`bde2020`); escribir `mapper.py`/`reducer.py`/`combiner.py` y sus
variantes de nivel 2 y 3 adaptados a las columnas reales de
`secop_sample.csv`; y redactar este documento.

Verifiqué las cifras clave ejecutando yo mismo los jobs en el clúster real
(no valores supuestos ni recordados de una sesión anterior): los
contadores de bytes de mezcla, registros de entrada/salida y grupos por
clave de cada sección de este documento salen directamente de la salida de
`hadoop jar ... -streaming` de cada ejecución citada por su `job_id`, y los
resultados de nivel 1 vs. nivel 2, y de nivel 3 sin vs. con combinador, se
compararon línea por línea con `Compare-Object` para confirmar
correctitud, no solo lectura de contadores.

**Actualización (2026-08-18):** usé Claude Code para escribir los scripts
de `hdfs-cluster-equipo/muestra_t1t3/` (adaptados a las 15 columnas de
`secop_sample_periodo2.csv`) y para ejecutar directamente los 4 jobs de la
sección 4 contra el clúster real que ya estaba corriendo (verificado con
`docker ps` y `mapred job -list all` antes de confiar en los resultados).
Los contadores de la sección 4 salen de la salida real de esos 4 jobs
(`job_1787058871039_0001` a `_0004`), y las comparaciones sin vs. con
combinador se hicieron con `diff` sobre los `part-00000` descargados de
HDFS — no son cifras estimadas ni reescaladas de la sección 1-3.

# T4 · MapReduce, contadores de mezcla y combinador — evidencia de ejecución

**Fuente:** `secop_sample.csv` — SECOP II, dataset "Procesos de Contratación"
(59 columnas, 200.000 filas). Distinto del dataset "Contratos Electrónicos"
(jbjy-vk9h) documentado en `docs/ficha_tecnica.md` del repo `proyecto-secop`;
se usó este por ser el único CSV de SECOP II disponible en la máquina al
momento de la práctica. Ver sección "Ausencias y desviaciones" al final.

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
| `PipeMapRed.waitOutputThreads(): subprocess failed with code 127` | Las imágenes `bde2020/hadoop-*` (Debian 9 stretch) no traen Python instalado | Se instaló `python3` en el contenedor `nodemanager` (repos de `archive.debian.org`, ya que stretch está EOL en `deb.debian.org`). **Este paso vive en la capa de escritura del contenedor: si se recrea el contenedor `nodemanager`, hay que reinstalarlo** — no está en el `docker-compose.yml` ni en una imagen propia todavía |
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

## 4. Reto de negocio · Nota técnica para gerencia

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

## 5. Ausencias y desviaciones (declaradas, no ocultas)

- **Fuente usada vs. fuente documentada en T1/T3:** esta práctica corrió
  sobre `secop_sample.csv` (dataset "Procesos de Contratación", 59
  columnas, 200.000 filas), no sobre `evidencia/secop_sample_periodo2.csv`
  (dataset "Contratos Electrónicos", 15 columnas) que documenta
  `docs/ficha_tecnica.md` en el repo `proyecto-secop` — ese archivo no
  estaba disponible en esta máquina. Antes de dar T4 por cerrada frente al
  resto del proyecto, el equipo debe decidir si repite esta práctica con el
  dataset oficial de T1/T3 o si documenta explícitamente que T4 usa una
  fuente SECOP II distinta.
- **Instalación de Python en el nodemanager** vive en la capa de escritura
  del contenedor (no en `docker-compose.yml` ni en una imagen propia): si
  alguien recrea el contenedor `nodemanager`, el job volverá a fallar con
  "subprocess failed with code 127" hasta reinstalarlo. Pendiente:
  convertir esto en un `Dockerfile` propio o un script de inicialización
  para que sea reproducible sin intervención manual.
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

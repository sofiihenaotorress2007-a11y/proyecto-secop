# T5 · El lago del proyecto

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean**
Equipo: Número 6 · Integrantes: Ana Sofía Henao Torres, Simón Robles Díaz, Samuel Esteban Gómez Alfonso
Fuente del proyecto: SECOP II — Contratos Electrónicos (Colombia Compra Eficiente, datos.gov.co)

> Evidencia técnica completa, con comandos y salidas reales, en
> `lago-equipo/EVIDENCIA_T5.md`. Este documento es el mapa resumido que
> pide la plantilla del curso.

---

## 1. El mapa del lago

| Cubo | Qué contiene | Estado en el proyecto hoy |
|---|---|---|
| `cruda` | El dato tal como llegó de SECOP II, sin transformar | Poblado con T5 — `secop_sample_periodo2.csv` cargado |
| `refinada` | El dato limpio, tipado y validado | Vacío por ahora; se poblará más adelante en el curso |
| `consolidada` | El dato modelado y agregado, listo para consumir | Vacío por ahora |

---

## 2. La convención de rutas

**Plantilla de la ruta en la capa cruda**
```
cruda/<fuente>/anio=YYYY/mes=MM/dia=DD/<archivo>.<ext>
```

**Un ejemplo real de nuestro dato**
```
cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv
```

**La convención de las otras dos capas**
```
refinada/<fuente>/anio=YYYY/mes=MM/dia=DD/<archivo>.parquet
consolidada/<agregado_o_pregunta_de_negocio>/anio=YYYY/parte-*.parquet
```

`refinada` conserva la misma partición por fecha que `cruda` (necesaria
para rastrear de qué extracción viene cada versión limpia — linaje),
aunque cambia el formato a Parquet (tipado, columnar). `consolidada` deja
de particionar por fecha de ingesta y pasa a particionar por el tema que
responde la tabla, porque a esa capa ya no se le pregunta "¿qué llegó tal
día?" sino "¿cuál es el consolidado de tal pregunta de negocio?".

---

## 3. La partición

**Por qué particionamos así**

Por **fecha de extracción del snapshot**, no por una fecha propia de cada
fila del CSV. SECOP II se recibe como un extracto periódico: un solo
archivo cuyo contenido cubre varios meses (`fecha_firma` va de enero a
octubre de 2024 en la muestra oficial), no un archivo por día como el
ejemplo genérico de la guía (acueducto, una lectura por día). Particionar
por `fecha_firma` exigiría partir las filas del archivo — eso es una
transformación, y la capa cruda no se transforma, se sube tal cual llega.
La pregunta real que se hace al operar el lago es "¿tengo la extracción de
esta fecha?", no "¿qué contratos se firmaron tal día?" — esa segunda
pregunta se responde consultando el contenido ya cargado, no la ruta del
archivo.

---

## 4. La regla de la capa cruda

**Declaración de inmutabilidad**
La capa cruda es inmutable: guarda el dato tal como llegó del portal y no
se edita nunca. La evidencia real de la sección 2 de `EVIDENCIA_T5.md`
muestra que incluso una sobrescritura accidental de la misma clave no
destruye la versión original, gracias al versionado activo.

**Dónde se corrigen los errores**
Los errores y las limpiezas se hacen en la capa refinada, nunca en la
cruda.

---

## 5. Evidencia del versionado

**Versionado activo en la capa cruda**
Sí. Configurado con `put_bucket_versioning`, `Status: Enabled` —
confirmado después con `get_bucket_versioning`, que devuelve
`{'Status': 'Enabled'}`.

**Prueba de que una versión anterior sigue recuperable**
```
Antes de sobrescribir:
  VersionId c69c507b... | Ultima: True  | 36.357.888 bytes

Despues de sobrescribir la misma clave con un archivo distinto:
  VersionId 3aacfce9... | Ultima: True  |     80.384 bytes
  VersionId c69c507b... | Ultima: False | 36.357.888 bytes

Recuperacion real de la version original por VersionId:
  bytes leidos: 36.357.888 (coincide exactamente con el archivo original)
```

Salida completa y comandos exactos en `lago-equipo/EVIDENCIA_T5.md`,
sección 2.

**Por qué el versionado protege la inmutabilidad**
Sin versionado, sobrescribir una clave reemplaza físicamente el objeto:
el archivo original desaparece sin dejar rastro. Con versionado activo,
la clave sigue devolviendo la versión más reciente en una lectura normal,
pero ninguna versión anterior se borra — sigue siendo recuperable por su
`VersionId`. Un error de carga deja de ser destructivo.

---

## 6. Cómo encontrar un dato · la prueba del analista

**Pregunta de ejemplo**
Un analista necesita la extracción de SECOP II del 18 de agosto de 2026.
¿Cuál es la ruta?

**Respuesta, derivada solo de la convención**
```
cruda/secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv
```

Se deduce solo con la plantilla de la sección 2, sin preguntarle a nadie
del equipo — esa es la evidencia del reto Power Humanise.

---

## 7. Reproducibilidad

**Comandos exactos para reconstruir el lago**
```bash
cd lago-equipo
docker compose up -d
cd ..
docker compose up -d jupyter
docker exec proyecto-secop-jupyter python src/ingesta/cargar_cruda.py \
  --fuente data/raw/secop_sample_periodo2.csv \
  --endpoint http://host.docker.internal:9002
```

**Declaración**
Confirmamos que estos comandos, corridos en este equipo con el lago
recién creado (cubos inexistentes), producen los mismos cubos, la misma
ruta particionada y el versionado activo — verificado ejecutándolos
nosotros mismos, no asumido. Detalle completo y salidas reales de cada
paso en `lago-equipo/EVIDENCIA_T5.md`.

---

## Declaración de uso de IA generativa

- **Herramienta usada:** Claude (Anthropic)
- **En qué parte:** diseño de `lago-equipo/docker-compose.yml` y
  diagnóstico del conflicto real de puerto con `hdfs-namenode`; diseño de
  la convención de partición por fecha de extracción (justificada por
  cómo se consulta el dato, no copiada del ejemplo genérico de la guía);
  escritura de `src/ingesta/cargar_cruda.py` y del script de evidencia de
  versionado; redacción de este documento y de `EVIDENCIA_T5.md`.
- **Qué se verificó ejecutando código real:** los tres cubos, la carga de
  la fuente oficial, el versionado activo y la recuperación de la versión
  original se corrieron contra un contenedor MinIO real (no simulado), y
  la recuperación se verificó comparando el tamaño en bytes leído contra
  el tamaño real del archivo en disco — no solo que el `VersionId`
  apareciera listado. Detalle completo en `lago-equipo/EVIDENCIA_T5.md`.

---

## Referencias

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Reis, J., y Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.

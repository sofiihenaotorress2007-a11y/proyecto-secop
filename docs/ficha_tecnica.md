# T1 · Ficha técnica de la fuente del proyecto

**Estudiante:** Ana Sofía Henao Torres
**Fuente elegida:** SECOP II — Contratos Electrónicos
**Fecha de elaboración:** 2026-08-02

---

## Bloque A · Identidad de la fuente

**Origen y responsable**
Entidad que publica: Agencia Nacional de Contratación Pública — Colombia Compra Eficiente.
Conjunto de datos: "SECOP II - Contratos Electrónicos", publicado en el portal nacional de datos abiertos.
URL exacta del conjunto: https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h
Fecha de consulta del portal (verificación de metadatos del dataset): 2026-08-02.

> **Nota de trazabilidad:** el archivo usado para las mediciones de esta ficha (`evidencia/secop_sample_periodo2.csv`) corresponde a una muestra de trabajo entregada como material de respaldo de la sesión 1, no a una descarga directa realizada por mí desde el portal en la fecha indicada arriba. **Antes de la entrega final, debo descargar mi propia copia desde la URL declarada, repetir las mediciones del Bloque B con ese archivo, y actualizar las cifras de esta ficha.** Se deja esta nota explícita para cumplir con el principio de que "una ausencia documentada es información válida; una ausencia silenciada es un campo vacío".

**Licencia y condiciones de uso**
El portal datos.gov.co opera bajo condiciones generales de uso que permiten el aprovechamiento libre y sin restricciones de los datos publicados, para cualquier persona natural o jurídica, con fines comerciales o no comerciales, incluyendo desarrollo de aplicaciones, análisis, investigación y control (fuente: https://herramientas.datos.gov.co/terminos). No se identificó una licencia Creative Commons o similar declarada de forma explícita a nivel del dataset individual; la cobertura legal proviene de los términos generales del portal.

**Formato y mecanismo de publicación**
Formato de archivo: CSV descargable directamente desde la interfaz del portal (Socrata), y también accesible vía API SODA (Socrata Open Data API) para descargas programáticas y por rango de fechas.
Mecanismo de obtención repetible: descarga manual desde la interfaz web, o consulta programática vía API con parámetros de fecha — este segundo mecanismo es el que se usará en S12-S13 para la ingesta incremental.

**Frecuencia declarada frente a frecuencia observada**
Frecuencia declarada por el portal: actualización continua (el dataset indica última actualización el mismo día de cada consulta, según metadatos públicos).
Frecuencia observada: dentro de la muestra de trabajo, las fechas de firma (`fecha_firma`) cubren un rango continuo mes a mes sin vacíos (enero a octubre de 2024, con conteos mensuales entre 3.835 y 4.715 contratos). Esto es consistente con una publicación de alta frecuencia, pero **no verifiqué directamente la frecuencia de actualización del snapshot descargable** (eso requiere comparar dos descargas hechas en días distintos, pendiente para cuando reemplace el archivo de evidencia por mi propia descarga).

**Estabilidad del esquema**
Con los datos disponibles: la muestra de trabajo tiene 15 columnas con tipos de dato estables (12 texto, 2 enteros, 1 decimal) sin nulos inesperados fuera del campo `observaciones`. **No pude comparar el esquema entre dos períodos publicados distintos**, porque solo dispongo de una muestra (ver nota de trazabilidad arriba). El portal reporta que el dataset completo tiene 85 columnas, frente a las 15 de esta muestra — esa diferencia sugiere que el esquema real es más amplio y debe verificarse directamente en una descarga propia antes de asumir estabilidad completa.

**Identificador estable de registro**
Columna candidata: `id_contrato`.
Evidencia: en la muestra de 44.400 filas, `id_contrato` no presenta ningún valor duplicado (0 duplicados verificados por código, ver `medicion.ipynb`, sección 4). Esto confirma unicidad **dentro de esta muestra**; la verificación de que el mismo identificador se mantiene estable entre dos descargas realizadas en momentos distintos queda pendiente hasta contar con una segunda descarga real.

---

## Bloque B · Mediciones propias

| Medición | Valor | Unidad | Código que la produjo |
|---|---|---|---|
| S₀ (tamaño en disco) | 0,033861 | GB | `medicion.ipynb`, sección 1 |
| k (factor de expansión, `deep=True`) | 1,7857 | adimensional | `medicion.ipynb`, sección 2 |
| M total (RAM instalada) | 24,0 | GB | `medicion.ipynb`, sección 3 |
| M disponible (útil en el momento de medir) | 13,6 | GB | `medicion.ipynb`, sección 3 |

**Nota sobre M:** el notebook se ejecuta en Google Colab, que corre sobre una máquina virtual de Google, no sobre mi computador. Por esa razón no usé `psutil.virtual_memory()` (mediría la RAM del servidor de Colab, no la mía). En su lugar medí mi RAM directamente en mi equipo: la RAM total (24,0 GB DDR5) la obtuve de Configuración del sistema de Windows → Información del sistema. La RAM disponible (13,6 GB) la obtuve del Administrador de tareas de Windows → pestaña Rendimiento → Memoria → campo "Disponible", con 10,1 GB en uso al momento de medir (memoria comprimida) y sin aplicaciones pesadas adicionales abiertas más allá de los procesos habituales del sistema y el navegador con Colab. Equipo: portátil Windows, procesador Intel Core i5-12450HX, 24 GB RAM DDR5 a 4800 MT/s.

**Período que cubre S₀:** la muestra corresponde a contratos con `fecha_firma` entre enero y octubre de 2024 (10 meses).

---

## Bloque C · Crecimiento y umbral

**Estimación de g**

*Método declarado:* dado que solo dispongo de una muestra (no de dos descargas en momentos distintos del portal), estimé g de forma indirecta: conté el número de contratos publicados por mes según su `fecha_firma` dentro de la propia muestra, excluí el primer y el último mes (riesgo de corte incompleto por el límite de la descarga), y calculé la tasa de crecimiento geométrica compuesta entre el primer y el último mes completo.

- Contratos en 2024-02 (primer mes completo): 4.238
- Contratos en 2024-09 (último mes completo): 4.500
- Períodos entre ambos: 7 meses
- **g mensual estimado: 0,86 %**

*Limitación explícita:* esta g mide el crecimiento en **número de contratos publicados por mes**, no directamente el crecimiento del tamaño en disco del dataset acumulado. Asumo que ambos son proporcionales (más contratos ⇒ más filas ⇒ más peso en disco a tasa aproximadamente constante por fila), pero no lo he verificado con una segunda medición real de tamaño de archivo en dos fechas de descarga distintas. Es un supuesto declarado, no una medición directa de crecimiento de S₀.

**Cálculo de t_umbral**

Fórmula: t_umbral = ln( M / (k · S₀) ) / ln(1 + g)

Se calculó en dos escenarios de S₀:
1. Con el S₀ de la muestra (0,0339 GB) — resultado poco informativo porque la muestra es mucho menor que la fuente real.
2. Con S₀ estimado del dataset completo, escalando proporcionalmente por número de filas: la muestra tiene 44.400 filas y el portal reporta 5.900.000 filas totales para el dataset completo. S₀ estimado = 4,500 GB. **Esta es una cota inferior**, porque el dataset completo tiene 85 columnas frente a las 15 de la muestra usada para la proporción.

| Escenario de M | t_umbral (S₀ muestra) | t_umbral (S₀ dataset completo, estimado) |
|---|---|---|
| M disponible real (13,6 GB) | 632,4 meses | **61,4 meses (~5,1 años)** |
| M = 8 GB | 570,5 meses | **−0,5 meses** |
| M = 16 GB | 651,4 meses | 80,4 meses (~6,7 años) |

Código completo en `medicion.ipynb`, secciones 5 y 6.

**Interpretación**

Con el S₀ de la muestra el resultado no es informativo: la muestra es demasiado pequeña frente a cualquier escenario de memoria, así que el umbral aparece artificialmente lejano. La interpretación correcta debe hacerse sobre el S₀ estimado del dataset completo.

Ahí el resultado, usando mi memoria disponible real (13,6 GB), da **t_umbral = 61,4 meses, aproximadamente 5,1 años**. Es un resultado intermedio coherente con los dos escenarios de referencia: con 8 GB la fuente completa ya estaría saturada (−0,5 meses), y con 16 GB el margen sería de 6,7 años; mi equipo, con 13,6 GB disponibles, cae naturalmente entre ambos. **Esto significa que, si mi proyecto usa el dataset completo de SECOP II tal como está hoy, tengo aproximadamente cinco años antes de que deje de caber en la memoria de mi equipo actual** — un horizonte que obliga a planear, desde el diseño inicial del pipeline (sesiones futuras del curso), alguna de las salidas ante la saturación: reducir el dato, procesarlo por trozos, o eventualmente distribuir.

Es notable que la conclusión cualitativa (esta fuente eventualmente satura un nodo único, y en el escenario de memoria más ajustado ya lo hace) se sostiene incluso con una g mucho más conservadora (0,86% medido) que la g de referencia usada en la práctica de clase (4%): la restricción de volumen es real y no depende de haber sobreestimado el crecimiento.

**Qué hacer si su fuente no crece, o si no puede estimar g:** no aplica en este caso — sí fue posible estimar g con evidencia propia dentro de la muestra disponible, aunque con la limitación metodológica declarada arriba (crecimiento en conteo de filas, no en tamaño de archivo verificado directamente).

---

## Declaración de uso de IA generativa

Usé Claude (Anthropic) como asistente durante todo el proceso de esta ficha: para estructurar el código de medición de k (recordándome el uso obligatorio de `deep=True`), para diseñar el método de estimación de g a partir de conteos mensuales dentro de la muestra, para la fórmula y el código de cálculo de t_umbral, y para la redacción y organización de este documento siguiendo la plantilla del enunciado.

Verifiqué las cifras clave ejecutando yo misma el código en `medicion.ipynb` y contrastando las salidas (S₀, k, duplicados de `id_contrato`, conteo mensual y g) con lo reportado en este documento. **Pendiente:** reemplazar la medición de M por la de mi propio equipo, y sustituir el archivo de evidencia por una descarga propia del portal antes de la entrega final, tal como se declara en las notas de trazabilidad del Bloque A y B.

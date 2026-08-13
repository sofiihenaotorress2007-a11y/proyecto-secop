# Reto de negocio — Sesión 3: ¿Por qué pagamos por guardar cada dato tres veces?

**Equipo:** [Equipo N0 6]
**Competencia:** Emprendimiento Sostenible

---

## La pregunta de la gerencia

La gerencia del acueducto revisó la factura de almacenamiento y preguntó directo:
*"¿por qué pagamos por guardar cada dato tres veces?"*. Esta es la respuesta del
equipo, con cifras, no con "así viene configurado".

## La respuesta corta

Pagamos el triple porque el dato que guardamos —el histórico de contratación
pública de SECOP II— **no se puede volver a capturar** si se pierde, y el costo
absoluto de la tercera copia es bajo frente al riesgo que evita.

## Las cifras que sostienen la respuesta

Con el volumen proyectado a 12 meses de nuestra fuente (4,987 GB):

| Factor R | Almacenamiento físico | Costo adicional vs. R anterior | Nodos que puede perder |
|---|---|---|---|
| 1 | 4,99 GB | — | 0 (cualquier falla pierde dato) |
| 2 | 9,97 GB | +4,99 GB | 1 |
| **3** | **14,96 GB** | **+4,99 GB** | **2** |

Pasar de factor 2 a factor 3 cuesta exactamente lo mismo que pasar de 1 a 2:
**4,99 GB adicionales**. No es un salto de precio creciente — es un costo lineal
y predecible. Lo que sí crece con cada copia es la tolerancia: con factor 3,
el sistema sigue funcionando aunque **dos de tres nodos de datos fallen al
mismo tiempo**.

## Dato crítico frente a dato regenerable

Esta es la distinción que justifica pagar el triple, y no es automática — depende
de qué tan reemplazable es el dato:

- **Dato crítico (nuestro caso):** el histórico de contratos públicos documenta
  procesos legales y financieros ya cerrados. Si un bloque se pierde sin réplica,
  no hay una fuente alterna que reconstruya esa información con la misma
  fidelidad y trazabilidad temporal. Perderlo no es "recalcular", es perder
  evidencia.
- **Dato regenerable (ejemplo, no nuestro caso):** una caché de resultados
  intermedios de un cálculo, o un archivo temporal de procesamiento. Si se
  pierde, se vuelve a generar corriendo el proceso de nuevo — cuesta tiempo de
  cómputo, no información.

Para dato regenerable, factor 2 o incluso factor 1 (sin réplica, apoyado en
poder recalcular) puede ser una decisión razonable. Para dato crítico como el
nuestro, factor 3 es la decisión defendible.

## Cuándo SÍ convendría explorar una alternativa a la triple copia completa

La guía de la sesión menciona los **códigos de borrado (erasure coding)** como
una alternativa que reduce el costo de almacenamiento frente a guardar tres
copias completas, aunque su mecánica queda fuera del alcance de esta sesión.
Recomendaríamos evaluarla si:

- El volumen creciera varios órdenes de magnitud (de gigabytes a decenas o
  cientos de terabytes), donde el costo de la tercera copia completa sí se
  vuelve una decisión financiera relevante, no marginal como en nuestro caso
  actual (15 GB físicos a los 12 meses).
- El equipo pudiera tolerar mayor complejidad operativa y algo de latencia
  adicional en la reconstrucción de dato ante una falla, a cambio de reducir
  el costo de almacenamiento frente a la réplica completa.

Con el volumen actual y proyectado de nuestra fuente, esa complejidad adicional
no se justifica: el ahorro que daría erasure coding sería marginal en términos
absolutos, mientras que el costo de operarlo correctamente no lo es.

## Recomendación final

**Factor de réplica 3**, sostenido por: (1) el dato es crítico y no regenerable,
(2) el costo absoluto es bajo (14,96 GB físicos a los 12 meses, en cualquier
clúster moderno), y (3) no hay evidencia de que el volumen vaya a crecer lo
suficiente en el corto plazo como para justificar la complejidad de una
alternativa como erasure coding.

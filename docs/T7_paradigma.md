# T7 · Decisión de paradigma — Proyecto SECOP II

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean**
Proyecto: SECOP II — Contratos Electrónicos

---

## Parte A · Tabla de asignación

| Requisito | Frescura exigida | Volumen por ciclo | Paradigma | Justificación |
|---|---|---|---|---|
| Carga periódica del dataset SECOP II al lago de datos | Días (una carga diaria o semanal es suficiente) | ~130–155 contratos nuevos por día si es carga incremental; el histórico completo son ~5,9 millones de registros / ~4,5 GB si se recarga entero | **Lotes** | La fuente crece de forma lenta y medible: ~0,86 % mensual (T1), es decir del orden de 150 contratos nuevos por día sobre un histórico de millones. Un lote diario o semanal sobra para esa tasa de crecimiento, y es mucho más barato que mantener infraestructura encendida. |
| Panel/dashboard del estado actual de contratos | Horas | Vista agregada sobre el histórico (~5,9 millones de registros) más unos cientos de registros nuevos desde el último refresco | **Casi real** (micro-lotes, refresco cada 2–4 horas) | Con ~150 contratos nuevos por día, un refresco cada pocas horas ya refleja fielmente el estado real; no hay volumen ni velocidad de cambio que justifique un flujo continuo. |
| Alerta de contratos con señales de riesgo (montos atípicos, plazos cortos) | Minutos a horas | Decenas de registros nuevos por ciclo (fracción de los ~130–155 contratos/día) | **Flujo o casi real** | Aunque el volumen es bajo, el valor de la alerta depende de la oportunidad: si llega días tarde, la ventana para revisar o cuestionar el contrato riesgoso ya se cerró. Aquí la frescura la exige el caso de uso, no el volumen. |

> Cifras de volumen y crecimiento tomadas de `docs/ficha_tecnica.md` (T1): dataset completo ≈ 5,9 millones de registros, 85 columnas, ≈ 4,5 GB estimados; crecimiento mensual observado ≈ 0,86 %.

---

## Parte B · Compromiso CAP declarado

Tomamos el requisito del **panel/alerta de contratos riesgosos**. Ante una caída de red entre el servicio de detección y el panel que consultan los usuarios, hay que elegir:

- **Consistencia:** dejar de responder hasta reconectar, para no mostrar un dato desactualizado.
- **Disponibilidad:** seguir mostrando la última alerta o el último estado conocido, aunque esté desactualizado.

**Decisión: disponibilidad.** Para una herramienta de transparencia de contratación pública, mostrar un dato con algunos minutos de antigüedad es mejor que dejar a los usuarios sin visibilidad alguna. No hay una transacción financiera en juego que exija coherencia inmediata (a diferencia de un saldo bancario); lo que sí importa es que el panel nunca desaparezca del todo, porque su valor está en mantener visibilidad continua sobre la contratación pública.

---

## Parte C · Defensa ante la gerencia

*La gerencia objeta el costo de la parte por flujo/casi real y pregunta por qué no ponemos todo por lotes.*

El requisito crítico es la **alerta de contratos con señales de riesgo**: exige frescura de minutos, no de días. Si ese dato llega tarde, se pierde la ventana para revisar, cuestionar o intervenir un contrato antes de que avance en su proceso — el valor de la alerta es precisamente anticiparse, y un lote nocturno la volvería inútil.

El resto de los requisitos —la carga del dataset y el panel general de estado— sí pueden ir por lotes o casi real, porque la fuente de datos (datos.gov.co) no se actualiza de forma continua: se publica en bloques periódicos. Mantenerlos por lotes ahorra el costo de tener infraestructura encendida las 24 horas para un dato que de todas formas no cambia segundo a segundo.

Por eso el híbrido es la opción correcta: cuesta menos que poner todo por flujo, porque solo el módulo de alertas se mantiene activo de forma continua; y arriesga menos que poner todo por lotes, porque no sacrifica la ventana de detección temprana que le da valor real al proyecto.

---

*Documento producido para la tarea T7 · Sesión 7 · IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean.*

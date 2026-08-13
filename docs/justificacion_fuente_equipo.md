# Consolidación de equipo — Justificación de la fuente elegida (T3, Paso cero)

**Equipo:** [Ana Sofia Henao Torres, Simón Robles Diaz, Samuel Esteban Gomez Alfonso]
**Fecha de decisión:** [12/08/2026]
**Integrantes y sus fuentes originales de T1:**

- Ana Sofía Henao Torres — SECOP II, Contratos Electrónicos (Colombia Compra Eficiente)
- Simón Robles Díaz — IDEAM, Temperatura Ambiente del Aire (versión final; la primera
  versión de su ficha usaba matrícula de educación superior del MinEducación, descartada
  antes de esta comparación)
- [tercer integrante] — [su fuente]

## Fuente elegida por el equipo: SECOP II — Contratos Electrónicos

## Los cuatro requisitos mínimos, verificados en las fuentes candidatas

| Requisito | SECOP II | IDEAM — Temperatura del Aire |
|---|---|---|
| Acceso público y licencia clara | Términos generales de datos.gov.co | CC BY-SA 4.0, declarada explícitamente |
| Publicación repetida en el tiempo | Continua, histórico desde 2019 | Diaria, con discrepancia real detectada entre frecuencia declarada y observada |
| Identificador estable de registro | `id_contrato`, único sin complicaciones | `codigoestacion + codigosensor + fechaobservacion`, verificada al 100% |
| Sin datos personales identificables | Entidades y empresas | Estaciones meteorológicas |

**Las dos fuentes candidatas cumplían los cuatro requisitos sin ambigüedad.** La
decisión no se tomó por descarte de requisitos mínimos, sino por criterio técnico
sobre cuál encaja mejor con el arco completo del curso.

## El criterio técnico decisivo

Las 30 sesiones del curso están construidas alrededor de la pregunta que abrió la
sesión 1: *el dato no cabe en un solo nodo, ¿qué se hace?* Al medir el umbral de
saturación (t_umbral) de cada fuente candidata en su ficha T1:

| Fuente | t_umbral | Interpretación |
|---|---|---|
| **SECOP II** | Negativo con M=8GB; ≈61 meses con memoria real de 13,6GB | **Ya cruzó el umbral hoy.** El problema de volumen es real y actual, no hipotético |
| **IDEAM — Temperatura del Aire** | ≈1.219 años con la ventana de crecimiento medida (incluso ≈25 años en el escenario más agresivo probado) | El volumen **nunca** será el problema de esta fuente, según su propia ficha |

Los módulos de arquitectura distribuida, réplica, particionamiento y procesamiento
distribuido (sesiones 3 a 20) requieren una fuente donde la restricción de volumen
sea genuina para que los ejercicios (factor de réplica, proyección de
almacenamiento, particionamiento) tengan sentido práctico y no solo teórico. SECOP
II cumple esa condición desde ahora; la fuente del IDEAM, según su propia ficha,
no la cumple bajo ningún escenario de crecimiento medido.

## Lo que se pierde y lo que se gana con esta elección

**Se gana:** una fuente con un problema de volumen real y demostrable, que da
sentido concreto a las próximas 17+ sesiones del módulo de arquitectura de datos.

**Se pierde, por ahora:** el trabajo de calidad de datos que Simón ya había
adelantado sobre su fuente (detección de anomalías, sensibilidad de la tasa de
crecimiento a la ventana de medición). Esa metodología no se descarta — se aplicará
sobre SECOP II cuando el curso llegue al módulo de calidad y veracidad (módulo 3),
reutilizando el mismo rigor ya demostrado.

## Decisión final

El equipo consolida su trabajo en el repositorio `proyecto-secop`
(`https://github.com/sofiihenaotorress2007-a11y/proyecto-secop`), sobre la fuente
**SECOP II — Contratos Electrónicos**, con la ficha técnica ya versionada en
`docs/ficha_tecnica.md`.

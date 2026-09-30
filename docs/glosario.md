# Glosario bilingüe acumulativo del equipo

Glosario técnico que se acumula sesión tras sesión. Cada término se agrega
una sola vez, con la sesión donde se incorporó.

| Español | Inglés | Precisión de uso | Agregado en |
|---|---|---|---|
| Nodo caído / fallo de nodo | node failure | El evento que la réplica está diseñada a tolerar, distinto de una corrupción de dato | S3 |
| Escritura / operación de escritura | write | La operación que debe propagarse a las réplicas; el punto donde aparece el compromiso entre consistencia y disponibilidad | S3 |
| Divergencia de réplicas | replica divergence | Cuando dos copias del mismo dato muestran valores distintos temporalmente, antes de converger | S3 |
| Arquitectura de referencia | reference architecture | El patrón general elegido para conectar los componentes del sistema (p. ej. vía única con flujo acotado, Lambda, malla de datos), del que se derivan las decisiones técnicas concretas | S8 |
| Diagrama de contexto (C4) | context diagram | Nivel 1 de C4: muestra el sistema como una sola caja, sus actores y los sistemas externos con los que intercambia datos, sin mostrar nada interno | S8 |
| Diagrama de contenedor (C4) | container diagram | Nivel 2 de C4: muestra las unidades de despliegue dentro del sistema (no confundir con "contenedor" de Docker) y cómo se comunican entre sí | S8 |
| Registro de decisión de arquitectura | Architecture Decision Record (ADR) | Documento versionado que registra una decisión de arquitectura puntual (no el sistema completo): título y estado, contexto, decisión y consecuencias, incluido al menos un costo aceptado | S9 |
| Lakehouse | lakehouse | Formato de almacenamiento que agrega transacciones ACID y viaje en el tiempo fila a fila sobre un lago de objetos (p. ej. Delta Lake, Iceberg); evaluado y descartado en `docs/adr/0001-almacenamiento.md` por no tener hoy un requisito transaccional real | S9 |
| Análisis de sensibilidad | sensitivity analysis | Verificar cuánto tendría que cambiar un peso de la matriz de decisión para que cambie la opción ganadora; una decisión robusta necesita un cambio grande, una sensible cambia con poco | S9 |
| Grano | grain | La frase, sin la conjunción "y", que declara qué representa exactamente una fila de la tabla de hechos; todo lo demás del modelo dimensional se justifica contra esa frase | S10 |
| Esquema en estrella | star schema | Una tabla de hechos rodeada de dimensiones planas y conformadas, cada una conectada directamente a los hechos (sin dimensiones intermedias) | S10 |
| Dimensión conformada | conformed dimension | Una dimensión compartida con el mismo significado y la misma clave subrogada en todos los hechos que la usan, para que se pueda cruzar información entre distintas tablas de hechos sin ambigüedad | S10 |
| Clave subrogada | surrogate key | Identificador propio del modelo dimensional (p. ej. entero autoincremental), distinto de la clave del sistema origen; conservada la clave de origen como atributo aparte, no reemplazada | S10 |
| Dimensión degenerada | degenerate dimension | Un identificador del sistema origen (p. ej. `id_contrato`) que se deja directamente en la tabla de hechos porque no tiene atributos descriptivos propios que ameriten su propia tabla de dimensión | S10 |
| Copo de nieve | snowflake schema | Normalizar una dimensión en varias tablas relacionadas entre sí (p. ej. departamento → región), evaluado en `docs/T10_modelo_dimensional.md` sección 5 y descartado por el bajo volumen actual del proyecto | S10 |

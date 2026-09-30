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

# Nivel 3 · Frontera del contenedor — decisión de diseño

**Proyecto:** proyecto-secop
**Autores:** Ana Sofía Henao Torres, Simon Robles Diaz, Samuel Gomez

## 1. Qué va en la imagen, qué se monta, qué se declara en compose

| Elemento | Dónde vive | Por qué ahí y no en otro lugar |
|---|---|---|
| Python, JupyterLab, motor de PostgreSQL | **Imagen** (oficiales: `quay.io/jupyter/scipy-notebook`, `postgres:16.4`) | No construyo una imagen propia. La guía de la sesión es explícita: *"Hoy usamos imágenes oficiales existentes. Construir imágenes propias llega cuando el stack lo exija"*. Mi proyecto no necesita nada fuera de lo que estas imágenes ya ofrecen, así que crear un `Dockerfile` propio sería complejidad sin beneficio. |
| Librerías de Python (pandas, numpy, matplotlib, sqlalchemy, psycopg2-binary) | **Se instalan al arrancar**, no están horneadas en la imagen | Decisión con una desventaja consciente: cada `docker compose up` vuelve a instalarlas (más lento que si estuvieran en una imagen propia ya construida con ellas). La ventaja: `requirements.txt` es la única fuente de verdad de las versiones, versionada en Git y editable sin reconstruir ninguna imagen. Para un proyecto de este tamaño, prioricé simplicidad de mantenimiento sobre velocidad de arranque. |
| Código y datos (`notebooks/`, `src/`, `data/`, `docs/`) | **Se montan** como volúmenes desde el host | Son las carpetas que cambian todo el tiempo mientras trabajo. Si estuvieran copiadas dentro de la imagen, cada cambio exigiría reconstruir la imagen — inviable para desarrollo activo. El montaje las mantiene sincronizadas en tiempo real entre mi disco y el contenedor. |
| Datos de PostgreSQL (`pgdata`) | **Volumen nombrado de Docker**, no montaje directo a una carpeta del host | A diferencia del código, los archivos internos de PostgreSQL no deben editarse a mano desde fuera del contenedor — hacerlo puede corromper la base de datos. Un volumen nombrado le da persistencia (los datos sobreviven a `docker compose down`) sin exponer la estructura interna al sistema de archivos del host. |
| Credenciales (`POSTGRES_USER`, `POSTGRES_PASSWORD`, etc.) | **Variables de entorno**, vía `.env` (no versionado) | Ni en la imagen ni en el código: si estuvieran escritas en `docker-compose.yml` o en el código Python, quedarían en el historial de Git de forma permanente, tal como advierte la sesión 2 sobre por qué las credenciales nunca entran a control de versiones. |
| Topología del proyecto (puertos, healthcheck, orden de arranque `depends_on`) | **Se declara en `docker-compose.yml`** | Es la "cocina" completa escrita como texto: qué servicios existen, cómo se conectan, en qué orden deben estar listos. Sin esto, dos personas levantarían el proyecto de formas distintas. |

## 2. La regla general que usé para decidir

Una pieza va **en la imagen** si es infraestructura estable que no cambio yo (el motor de Python, el motor de Postgres). Va **montada** si es algo que edito activamente durante el desarrollo (código, notebooks, datos de trabajo). Se **declara en compose** si es configuración de cómo las piezas se relacionan entre sí (puertos, dependencias, variables de entorno) en vez de ser contenido en sí mismo.

## 3. Reproducción en un entorno limpio

Para simular un "entorno limpio" en mi propio equipo (sin tener una segunda máquina disponible), ejecuté:

```bash
docker compose down -v
```

El flag `-v` es importante: no solo detiene y borra los contenedores, también **borra el volumen nombrado `pgdata`**, es decir, borra por completo los datos de PostgreSQL. Esto simula, dentro de lo posible en un solo equipo, el escenario de alguien que clona el repositorio por primera vez y no tiene absolutamente nada previo — ni contenedores, ni datos, ni configuración residual.

Luego de recrear `.env` a partir de `.env.example` (el único paso manual documentado en el README), volví a ejecutar:

```bash
docker compose up
```

Y el proyecto se levantó de nuevo sin intervención adicional: PostgreSQL arrancó limpio, el `healthcheck` confirmó que estaba listo, Jupyter esperó correctamente antes de arrancar, instaló las dependencias, y el cuaderno de verificación corrió completo incluyendo la conexión a la base de datos recién creada.

## 4. Qué falló durante la construcción (documentado, no ocultado)

La guía pide explícitamente documentar qué falló al reproducir, porque eso es información más valiosa que una carga exitosa. Estos son los tres fallos reales que encontré, con causa y corrección:

| # | Qué falló | Causa raíz | Corrección |
|---|---|---|---|
| 1 | `docker compose up` fallaba con `Error: failed to resolve reference "docker.io/jupyter/scipy-notebook:2024-01-15"` | Usé un tag de imagen que no existe. Además, las imágenes de Jupyter se movieron de Docker Hub a Quay.io desde 2023; Docker Hub dejó de actualizarlas. | Cambié la imagen a `quay.io/jupyter/scipy-notebook:2026-07-28`, un tag verificado como existente en el registro correcto. |
| 2 | Instalación de dependencias fallaba compilando `pandas` desde código fuente (`ninja: build stopped: subcommand failed`) | La imagen trae Python 3.13. `pandas==2.2.2` no tiene un paquete precompilado (wheel) para esa versión de Python, así que pip intentaba compilarlo desde cero y fallaba por falta de herramientas de compilación. | Actualicé a `pandas==2.2.3`, versión que sí publica wheels para Python 3.13. Mismo ajuste para `numpy` (a `2.1.1`) y `matplotlib` (a `3.9.2`). |
| 3 | Instalación fallaba en `psycopg2-binary` con `Error: pg_config executable not found` | Mismo problema de fondo que el #2: `psycopg2-binary==2.9.9` tampoco publicaba wheel para Python 3.13 en el momento de la instalación, así que intentaba compilar desde fuente y necesitaba herramientas de PostgreSQL que el contenedor de Jupyter no tiene por diseño. | Actualicé a `psycopg2-binary==2.9.10`, versión posterior con soporte de wheel para Python 3.13. |

**Lección general que me deja esto:** "anclar una versión" no es solo escribir cualquier número exacto — es anclar a una versión que además sea **compatible con el resto del entorno** (en este caso, con la versión de Python que trae la imagen base). Anclar a una versión incompatible produce el mismo problema de raíz que no anclar nada: el entorno no se levanta igual en todas partes, solo que ahora falla en vez de instalar algo distinto silenciosamente.

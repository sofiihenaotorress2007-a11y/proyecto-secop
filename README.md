# Proyecto SECOP II — Big Data e Ingeniería de Datos

Proyecto del semestre para la asignatura IFPN0025, construido sobre la fuente
**SECOP II — Contratos Electrónicos** (Colombia Compra Eficiente / datos.gov.co).

## Qué necesita para levantar este proyecto

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git

No necesita instalar Python, pandas, PostgreSQL, ni ninguna librería en su
equipo: todo corre dentro de los contenedores.

## Configurar variables de entorno (obligatorio antes del primer levantamiento)

Este proyecto usa un segundo servicio, PostgreSQL, que requiere credenciales.
Esas credenciales **nunca se versionan en Git**. Antes de levantar el
proyecto por primera vez:

```bash
cp .env.example .env
```

y edite `.env` con sus propios valores (o deje los de ejemplo si solo va a
usarlo localmente).

## Cómo se levanta (un solo comando)

```bash
docker compose up
```

Esto levanta dos servicios:
- **db**: PostgreSQL 16.4, con los datos persistidos en un volumen de Docker
- **jupyter**: espera a que `db` esté saludable (`healthcheck`), instala las
  dependencias ancladas en `requirements.txt`, y expone Jupyter en:

```
http://localhost:8888
```

Ábralo en su navegador. Debería ver la carpeta `work/` con `notebooks/`, `src/`,
`data/` y `docs/`.

## Cómo se conectan los dos servicios entre sí

Jupyter no se conecta a PostgreSQL usando `localhost`, sino usando el
**nombre del servicio** declarado en `docker-compose.yml` (`db`). Docker
Compose crea automáticamente una red interna donde cada servicio puede
alcanzar a los demás por su nombre. Las credenciales se pasan a ambos
contenedores vía `.env`, nunca escritas directamente en el código.

## Cómo se verifica que funcionó

Abra `notebooks/00_verificacion.ipynb` y ejecútelo completo
(Run → Run All Cells). Si todas las celdas corren sin error — incluida la
última, que confirma la conexión a PostgreSQL — el entorno está
correctamente levantado.

## Cómo se apaga

```bash
docker compose down
```

## Estructura del proyecto

```
proyecto-secop/
├── README.md              # este archivo, el contrato del proyecto
├── docker-compose.yml      # declara el servicio de Jupyter y sus versiones
├── requirements.txt        # dependencias de Python con versión anclada
├── .gitignore               # protege datos y credenciales de subirse a Git
├── data/
│   └── raw/                # dato crudo, NUNCA se versiona en Git
├── notebooks/
│   └── 00_verificacion.ipynb
├── src/                     # código reutilizable (no cuadernos sueltos)
└── docs/
    └── ficha_tecnica.md    # T1: ficha técnica de la fuente
```

## Datos

Los datos de este proyecto (SECOP II) no están incluidos en este repositorio,
siguiendo la regla de que los datos nunca se versionan en Git. Descárguelos
desde:

https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h

y colóquelos en `data/raw/`.

## Fuente del proyecto

Ver `docs/ficha_tecnica.md` para el detalle completo de origen, licencia,
mediciones de volumen y cálculo del umbral de saturación de esta fuente.

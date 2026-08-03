# Guía de incorporación — Proyecto SECOP II

Bienvenida/o al equipo. Esta guía te lleva de cero a tener el proyecto corriendo
en tu computador, sin necesidad de preguntarle nada a nadie. Si en algún punto
necesitas preguntar algo, es porque esta guía tiene un vacío — avísanos.

## Antes de empezar: qué vas a necesitar

Solo dos programas, ninguno relacionado con Python ni con bases de datos:

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — descárgalo, instálalo, y ábrelo. Espera a que abajo a la izquierda diga **"Engine running"**.
2. **Git** — si no sabes si lo tienes, abre una terminal (en Windows: busca "Símbolo del sistema" o "PowerShell" en el menú de inicio) y escribe `git --version`. Si te muestra un número de versión, ya lo tienes.

No necesitas instalar Python, pandas, PostgreSQL, ni nada más. Todo corre dentro de contenedores.

## Paso 1 · Consigue el código

```bash
git clone <URL-del-repositorio>
cd proyecto-secop
```

## Paso 2 · Crea tu archivo de credenciales locales

El repositorio no trae credenciales (por seguridad, nunca se suben a Git). Trae una plantilla:

```bash
cp .env.example .env
```

Con eso basta para uso local — no necesitas cambiar nada dentro de `.env` a menos que alguien del equipo te diga lo contrario.

## Paso 3 · Levanta todo con un solo comando

```bash
docker compose up
```

La primera vez tarda varios minutos: descarga las imágenes de Jupyter y PostgreSQL, e instala las librerías de Python. Verás mucho texto pasando — es normal. Sabes que terminó cuando ves una línea como:

```
Jupyter Server ... is running at:
http://localhost:8888/lab
```

## Paso 4 · Verifica que todo funciona

Abre tu navegador en:
```
http://localhost:8888
```

Entra a `notebooks/00_verificacion.ipynb` y corre todas las celdas (**Run → Run All Cells**). Si la última celda te muestra un mensaje de conexión exitosa a PostgreSQL, tu entorno está listo. Ya puedes trabajar.

## Paso 5 · Cuando termines por hoy

```bash
docker compose down
```

Esto apaga los contenedores pero conserva tus datos (no uses `-v` a menos que quieras borrar la base de datos completa).

## Si algo falla

Estos son los tres problemas reales que ya nos pasaron a nosotros al construir este proyecto — si te topas con algo parecido, ya sabemos la causa:

| Si ves este error... | Es porque... | Qué hacer |
|---|---|---|
| `failed to resolve reference` al hacer `docker compose up` | El tag de una imagen en `docker-compose.yml` no existe en el registro | Avísanos, puede que necesitemos actualizar el tag a una versión vigente |
| La instalación se queda compilando `pandas` (o cualquier librería) por mucho tiempo y falla | La versión anclada en `requirements.txt` no tiene un paquete precompilado para la versión de Python de la imagen | Avísanos para actualizar la versión anclada, no lo edites tú sin avisar — afecta a todo el equipo |
| El navegador dice "Kernel does not exist" al abrir un notebook | Quedó una pestaña vieja del navegador de una sesión anterior de Docker | Cierra esa pestaña, refresca, y vuelve a abrir `http://localhost:8888` |

## La regla de oro de este proyecto

Todo lo que necesitas para trabajar está en este repositorio y en este README. Si alguna vez tienes que hacer algo que no está escrito aquí, avísanos — significa que el proyecto dejó de ser reproducible para alguien más, y eso es justo lo que queremos evitar.

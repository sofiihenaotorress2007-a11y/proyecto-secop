# Lago de datos del equipo · MinIO

Almacenamiento de objetos (MinIO) usado para la práctica de la sesión 5 y
la tarea T5 — evidencia completa en `EVIDENCIA_T5.md`.

## Cómo levantar el lago

```bash
cd lago-equipo
docker compose up -d
```

Consola web: http://localhost:9001 (usuario/contraseña en `../.env`,
variables `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`).

API S3: `http://localhost:9002` desde el host, o
`http://host.docker.internal:9002` desde otro contenedor Docker Desktop
(ej. el de Jupyter). **No es el puerto 9000 de la guía del curso** — ese
puerto ya lo usa `hdfs-namenode` en este proyecto; ver la sección 0 de
`EVIDENCIA_T5.md` para el detalle del conflicto y la corrección.

## Cómo cargar la fuente cruda

Con el contenedor de Jupyter arriba (`docker compose up -d jupyter` desde
la raíz del repo, ya trae `boto3` vía `requirements.txt`):

```bash
docker exec proyecto-secop-jupyter python src/ingesta/cargar_cruda.py \
  --fuente data/raw/secop_sample_periodo2.csv \
  --endpoint http://host.docker.internal:9002
```

Crea los tres cubos (`cruda`, `refinada`, `consolidada`) si no existen,
activa el versionado en `cruda`, y sube el archivo bajo
`secop/anio=YYYY/mes=MM/dia=DD/<archivo>` (fecha de extracción, no fecha
de las filas — justificado en `EVIDENCIA_T5.md`, sección 3).

## Para apagar

```bash
docker compose down
```

El volumen `./datos_lago` persiste el contenido entre reinicios (no
versionado en Git, ver `.gitignore`). Para empezar de cero:

```bash
docker compose down
rm -rf datos_lago
docker compose up -d
```

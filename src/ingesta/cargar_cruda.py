#!/usr/bin/env python3
"""Ingesta de la fuente cruda del equipo al lago de datos (MinIO).

Uso:
    python src/ingesta/cargar_cruda.py --fuente ruta/al/archivo.csv

Crea los tres cubos del lago si no existen (cruda, refinada,
consolidada), activa el versionado en `cruda`, y sube el archivo con la
clave `<fuente>/anio=YYYY/mes=MM/dia=DD/<nombre_archivo>`.

Por que la fecha de la ruta es la fecha de EXTRACCION del snapshot, y no
una fecha por fila del CSV: la fuente del equipo (SECOP II) es un
extracto periodico que cubre varios meses de datos (`fecha_firma` va de
enero a octubre de 2024 en la muestra oficial), no un archivo por dia
como el ejemplo de la guia (acueducto). Partir el archivo por
`fecha_firma` para encajar en particiones diarias exigiria transformar el
contenido, lo que viola la regla de inmutabilidad de la cruda: el dato se
sube tal como llego del portal, no se reescribe. Por eso la particion
representa cuando el equipo extrajo este snapshot, no el contenido
interno del archivo.
"""
import argparse
import datetime
import os
import sys

import boto3

CUBOS = ["cruda", "refinada", "consolidada"]


def cliente_s3(endpoint):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        region_name="us-east-1",
    )


def asegurar_cubos(s3):
    for cubo in CUBOS:
        try:
            s3.create_bucket(Bucket=cubo)
            print(f"Cubo creado: {cubo}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"El cubo ya existe: {cubo}")


def activar_versionado(s3, cubo="cruda"):
    s3.put_bucket_versioning(
        Bucket=cubo,
        VersioningConfiguration={"Status": "Enabled"},
    )
    print(f"Versionado activo en el cubo: {cubo}")


def construir_clave(fuente, fecha, nombre_archivo):
    return (
        f"{fuente}/anio={fecha.year:04d}/mes={fecha.month:02d}"
        f"/dia={fecha.day:02d}/{nombre_archivo}"
    )


def cargar(s3, ruta_archivo, fuente, fecha, cubo="cruda"):
    nombre_archivo = os.path.basename(ruta_archivo)
    clave = construir_clave(fuente, fecha, nombre_archivo)
    s3.upload_file(ruta_archivo, cubo, clave)
    print(f"Objeto cargado: s3://{cubo}/{clave}")
    return clave


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fuente", required=True, help="Ruta local del archivo a cargar")
    ap.add_argument(
        "--nombre-fuente",
        default="secop",
        help="Prefijo de la fuente en la clave (default: secop)",
    )
    ap.add_argument(
        "--fecha",
        default=None,
        help="Fecha de extraccion AAAA-MM-DD (default: hoy)",
    )
    ap.add_argument(
        "--endpoint",
        default=os.environ.get("MINIO_ENDPOINT"),
        help="Endpoint de la API S3 de MinIO (default: variable MINIO_ENDPOINT)",
    )
    args = ap.parse_args()

    if not args.endpoint:
        sys.exit("Falta MINIO_ENDPOINT (variable de entorno o --endpoint)")

    fecha = (
        datetime.date.fromisoformat(args.fecha)
        if args.fecha
        else datetime.date.today()
    )

    s3 = cliente_s3(args.endpoint)
    asegurar_cubos(s3)
    activar_versionado(s3, "cruda")
    cargar(s3, args.fuente, args.nombre_fuente, fecha)


if __name__ == "__main__":
    main()

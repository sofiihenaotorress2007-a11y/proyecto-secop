#!/usr/bin/env python3
"""Utilidades compartidas por los scripts de T6 para hablar con el lago (MinIO)."""
import os
import sys

import boto3


def cliente_s3(endpoint=None):
    endpoint = endpoint or os.environ.get("MINIO_ENDPOINT")
    if not endpoint:
        sys.exit("Falta MINIO_ENDPOINT (variable de entorno o --endpoint)")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        region_name="us-east-1",
    )


def ultima_clave_csv(s3, cubo="cruda", prefijo="secop/"):
    """Clave del CSV crudo mas reciente bajo el prefijo (ordena por fecha de
    extraccion, que va codificada en la ruta anio=/mes=/dia=)."""
    paginador = s3.get_paginator("list_objects_v2")
    claves = [
        obj["Key"]
        for pagina in paginador.paginate(Bucket=cubo, Prefix=prefijo)
        for obj in pagina.get("Contents", [])
        if obj["Key"].endswith(".csv")
    ]
    if not claves:
        sys.exit(f"No hay ningun CSV bajo s3://{cubo}/{prefijo}")
    return sorted(claves)[-1]


def descargar_csv_crudo(s3, ruta_local, cubo="cruda", prefijo="secop/", clave=None):
    """Descarga el CSV crudo a una ruta local temporal. No modifica ni borra
    el objeto original en `cruda`. Devuelve la clave descargada."""
    clave = clave or ultima_clave_csv(s3, cubo, prefijo)
    s3.download_file(cubo, clave, ruta_local)
    return clave

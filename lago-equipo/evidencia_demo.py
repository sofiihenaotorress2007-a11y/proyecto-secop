#!/usr/bin/env python3
"""Script de evidencia para T5 (Niveles 1 y 2 de la guia S05_P4): listado
por prefijo, y sobrescritura + versionado sobre la fuente ya cargada por
src/ingesta/cargar_cruda.py. No es parte del pipeline de ingesta oficial;
se corre desde la raiz del repo (usa rutas relativas a esa raiz):

    docker exec proyecto-secop-jupyter python lago-equipo/evidencia_demo.py
"""
import os

import boto3

ENDPOINT = os.environ["MINIO_ENDPOINT"]
CLAVE = "secop/anio=2026/mes=08/dia=18/secop_sample_periodo2.csv"

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=os.environ["MINIO_ROOT_USER"],
    aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    region_name="us-east-1",
)

print("=== Nivel 1: listado por prefijo (la ruta es clave, no carpeta) ===")
resp = s3.list_objects_v2(Bucket="cruda", Prefix="secop/anio=2026/")
for obj in resp.get("Contents", []):
    print("Clave:", obj["Key"], "| Tamano:", obj["Size"])

print()
print("=== head_object: confirma que el objeto existe (autoverificacion Nivel 1) ===")
h = s3.head_object(Bucket="cruda", Key=CLAVE)
print("VersionId de esta version:", h.get("VersionId"), "| ETag:", h.get("ETag"))

print()
print("=== Nivel 2: version ANTES de sobrescribir ===")
v_antes = s3.list_object_versions(Bucket="cruda", Prefix=CLAVE)
for v in v_antes.get("Versions", []):
    print("VersionId:", v["VersionId"], "| Ultima:", v["IsLatest"], "| Tamano:", v["Size"])

# Simula una sobrescritura accidental: sube una version truncada (primeras
# 100 lineas) bajo la MISMA clave, para demostrar que el versionado
# protege el original sin necesidad de "corregir" nada a mano.
ruta_original = "data/raw/secop_sample_periodo2.csv"
ruta_truncada = "/tmp/secop_sample_periodo2_truncado.csv"
with open(ruta_original, encoding="utf-8") as f_in, open(
    ruta_truncada, "w", encoding="utf-8"
) as f_out:
    for i, linea in enumerate(f_in):
        if i >= 100:
            break
        f_out.write(linea)

print()
print("=== Sobrescribiendo la misma clave con un archivo distinto (simulacion de error) ===")
s3.upload_file(ruta_truncada, "cruda", CLAVE)
print("Sobrescritura completada sobre la misma clave:", CLAVE)

print()
print("=== Nivel 2: versiones DESPUES de sobrescribir ===")
v_despues = s3.list_object_versions(Bucket="cruda", Prefix=CLAVE)
for v in v_despues.get("Versions", []):
    print("VersionId:", v["VersionId"], "| Ultima:", v["IsLatest"], "| Tamano:", v["Size"])

print()
print("=== Recuperando la version ORIGINAL (no la ultima) por su VersionId ===")
versiones_ordenadas = sorted(
    v_despues.get("Versions", []), key=lambda v: v["LastModified"]
)
version_original = versiones_ordenadas[0]
obj_recuperado = s3.get_object(
    Bucket="cruda", Key=CLAVE, VersionId=version_original["VersionId"]
)
contenido = obj_recuperado["Body"].read()
print(
    "Version original recuperada, VersionId:",
    version_original["VersionId"],
    "| bytes leidos:",
    len(contenido),
    "| coincide con tamano original esperado (36357888):",
    len(contenido) == 36357888,
)

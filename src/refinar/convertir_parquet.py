#!/usr/bin/env python3
"""Convierte el CSV crudo del lago a Parquet y lo sube, particionado, a la
capa refinada.

Uso:
    python src/refinar/convertir_parquet.py --codec zstd \
        --endpoint http://host.docker.internal:9002

Por que particiona por `fecha_firma` (anio/mes) y no por la fecha de
extraccion como la capa cruda: la refinada ya es dato tipado y
consultable, y las preguntas reales sobre SECOP II filtran por cuando se
firmo el contrato ("contratos de marzo de 2024"), no por cuando el equipo
extrajo el snapshot. Particionar por fecha_firma es lo que permite la
poda de particiones en DuckDB (ver docs/T6_formato.md, seccion 3). El CSV
en `cruda` solo se lee, nunca se modifica ni se borra.
"""
import argparse
import glob
import os
import tempfile

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.dataset as ds

from lago_utils import cliente_s3, descargar_csv_crudo

CODECS_VALIDOS = ["snappy", "gzip", "zstd"]


def leer_con_particion(ruta_csv):
    tabla = pv.read_csv(ruta_csv)
    fecha = tabla["fecha_firma"]
    if pa.types.is_string(fecha.type):
        fecha = pc.strptime(fecha, format="%Y-%m-%d", unit="s")
    tabla = tabla.append_column("anio", pc.strftime(fecha, format="%Y"))
    tabla = tabla.append_column("mes", pc.strftime(fecha, format="%m"))
    return tabla


def escribir_particionado(tabla, carpeta_local, codec):
    ds.write_dataset(
        tabla,
        base_dir=carpeta_local,
        format="parquet",
        partitioning=ds.partitioning(
            pa.schema([("anio", pa.string()), ("mes", pa.string())]), flavor="hive"
        ),
        file_options=ds.ParquetFileFormat().make_write_options(compression=codec),
        existing_data_behavior="overwrite_or_ignore",
    )


def subir_particiones(s3, carpeta_local, cubo, fuente):
    subidos = []
    for ruta in glob.glob(os.path.join(carpeta_local, "**", "*.parquet"), recursive=True):
        rel = os.path.relpath(ruta, carpeta_local).replace(os.sep, "/")
        clave = f"{fuente}/{rel}"
        s3.upload_file(ruta, cubo, clave)
        subidos.append(clave)
    return subidos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--codec",
        choices=CODECS_VALIDOS,
        required=True,
        help="Codec elegido, justificado con los numeros de medir_codecs.py",
    )
    ap.add_argument("--nombre-fuente", default="secop")
    ap.add_argument("--endpoint", default=os.environ.get("MINIO_ENDPOINT"))
    args = ap.parse_args()

    s3 = cliente_s3(args.endpoint)

    with tempfile.TemporaryDirectory() as tmp:
        ruta_csv = os.path.join(tmp, "cruda.csv")
        clave_origen = descargar_csv_crudo(
            s3, ruta_csv, cubo="cruda", prefijo=f"{args.nombre_fuente}/"
        )
        print(f"CSV crudo leido de: s3://cruda/{clave_origen} (no se modifica)")

        tabla = leer_con_particion(ruta_csv)
        print(
            f"Filas: {tabla.num_rows} | Columnas: {tabla.num_columns} "
            "(incluye anio, mes derivadas de fecha_firma)"
        )

        carpeta_parquet = os.path.join(tmp, "parquet")
        escribir_particionado(tabla, carpeta_parquet, args.codec)

        subidos = subir_particiones(s3, carpeta_parquet, "refinada", args.nombre_fuente)
        print(f"{len(subidos)} particiones subidas a s3://refinada/{args.nombre_fuente}/ con codec {args.codec}")
        for clave in sorted(subidos):
            print(f"  s3://refinada/{clave}")


if __name__ == "__main__":
    main()

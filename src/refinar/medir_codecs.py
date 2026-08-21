#!/usr/bin/env python3
"""Mide los tres codecs de Parquet (snappy, gzip, zstd) sobre la misma
muestra del CSV crudo del lago, y compara una consulta selectiva con
DuckDB contra la misma consulta sobre el CSV.

Uso:
    python src/refinar/medir_codecs.py --endpoint http://host.docker.internal:9002

Mide la mediana de 3 corridas por metrica: la primera lectura suele ser
mas lenta porque el archivo aun no esta en el cache del sistema operativo,
y una sola medicion no sustenta ninguna decision. Los tres codecs se
miden sobre la misma descarga del CSV crudo, no sobre muestras distintas.
"""
import argparse
import os
import tempfile
import time

import duckdb
import pyarrow.csv as pv
import pyarrow.parquet as pq

from lago_utils import cliente_s3, descargar_csv_crudo

CODECS = ["snappy", "gzip", "zstd"]
COLUMNAS_CONSULTA = ["fecha_firma", "valor_contrato"]


def mediana_tiempo(funcion, repeticiones=3):
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        funcion()
        tiempos.append(time.perf_counter() - t0)
    tiempos.sort()
    return tiempos[len(tiempos) // 2]


def medir_codecs(ruta_csv, carpeta_tmp):
    tabla = pv.read_csv(ruta_csv)
    tam_csv = os.path.getsize(ruta_csv)
    resultados = []
    for codec in CODECS:
        ruta = os.path.join(carpeta_tmp, f"muestra_{codec}.parquet")
        t_escritura = mediana_tiempo(lambda r=ruta, c=codec: pq.write_table(tabla, r, compression=c))
        tam = os.path.getsize(ruta)
        t_lectura = mediana_tiempo(lambda r=ruta: pq.read_table(r, columns=COLUMNAS_CONSULTA))
        resultados.append((codec, tam, t_escritura, t_lectura))
    return tabla, tam_csv, resultados


def comparar_duckdb(ruta_csv, ruta_parquet_elegido):
    consulta_parquet = f"""
        SELECT departamento, avg(valor_contrato) AS valor_promedio
        FROM read_parquet('{ruta_parquet_elegido}')
        WHERE valor_contrato IS NOT NULL
        GROUP BY departamento
    """
    consulta_csv = f"""
        SELECT departamento, avg(valor_contrato) AS valor_promedio
        FROM read_csv_auto('{ruta_csv}')
        WHERE valor_contrato IS NOT NULL
        GROUP BY departamento
    """

    def cronometrar(sql, repeticiones=3):
        return mediana_tiempo(lambda: duckdb.sql(sql).fetchall(), repeticiones)

    t_parquet = cronometrar(consulta_parquet)
    t_csv = cronometrar(consulta_csv)
    filas_parquet = duckdb.sql(consulta_parquet).fetchall()
    filas_csv = duckdb.sql(consulta_csv).fetchall()
    return consulta_parquet, t_parquet, t_csv, sorted(filas_parquet) == sorted(filas_csv)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nombre-fuente", default="secop")
    ap.add_argument("--endpoint", default=os.environ.get("MINIO_ENDPOINT"))
    ap.add_argument(
        "--codec-consulta",
        default="zstd",
        choices=CODECS,
        help="Codec del Parquet usado en la comparacion DuckDB de la seccion 3",
    )
    args = ap.parse_args()

    s3 = cliente_s3(args.endpoint)

    with tempfile.TemporaryDirectory() as tmp:
        ruta_csv = os.path.join(tmp, "muestra.csv")
        clave = descargar_csv_crudo(s3, ruta_csv, cubo="cruda", prefijo=f"{args.nombre_fuente}/")
        print(f"Muestra descargada de: s3://cruda/{clave} (no se modifica el original)\n")

        tabla, tam_csv, resultados = medir_codecs(ruta_csv, tmp)

        print(f"Filas: {tabla.num_rows} | Columnas: {tabla.num_columns}")
        print(f"{'Formato':<12}{'Tamano (bytes)':>16}{'Escritura (s)':>16}{'Lectura sel. (s)':>18}")
        print(f"{'CSV':<12}{tam_csv:>16}{'-':>16}{'-':>18}")
        for codec, tam, te, tl in resultados:
            reduccion = 100 * (1 - tam / tam_csv)
            print(f"{codec:<12}{tam:>16}{te:>16.3f}{tl:>18.3f}   (-{reduccion:.0f}% vs CSV)")

        ruta_elegido = os.path.join(tmp, f"muestra_{args.codec_consulta}.parquet")
        consulta, t_parquet, t_csv, igual = comparar_duckdb(ruta_csv, ruta_elegido)
        print(f"\nConsulta selectiva (DuckDB) con Parquet {args.codec_consulta}:")
        print(consulta.strip())
        print(f"Parquet: {t_parquet:.4f} s")
        print(f"CSV:     {t_csv:.4f} s")
        print(f"Mismo resultado en ambos: {igual}")


if __name__ == "__main__":
    main()

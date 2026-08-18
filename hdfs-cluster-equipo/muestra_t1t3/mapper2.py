#!/usr/bin/env python3
# Igual que mapper.py, pero emite valor_contrato,1 (suma parcial=el
# propio valor, conteo=1) para que combiner.py pueda agregarlos antes de
# la mezcla, y reducer2.py sume sumas y conteos en vez de promediar
# directamente. El combinador puede correr 0, 1 o varias veces, por eso
# su entrada y su salida deben compartir el mismo formato (suma,conteo).
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "id_contrato":
        continue
    if len(campos) < 15:
        continue
    departamento, valor_contrato = campos[8], campos[6]
    try:
        valor_contrato = float(valor_contrato)
    except ValueError:
        continue
    print("{0}\t{1},1".format(departamento, valor_contrato))

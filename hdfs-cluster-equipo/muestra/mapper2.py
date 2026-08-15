#!/usr/bin/env python3
# Igual que mapper.py, pero emite el conteo (1) junto al precio desde el
# inicio: departamento_entidad <tab> precio_base,1
#
# Es necesario para que combiner.py sea idempotente respecto al numero de
# veces que Hadoop decida ejecutarlo (cero, una o varias veces): su entrada
# y su salida deben tener siempre el mismo formato "suma,conteo".
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta.
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "entidad":
        continue
    if len(campos) < 21:
        continue
    departamento, precio_base = campos[2], campos[20]
    try:
        precio_base = float(precio_base)
    except ValueError:
        continue
    print("{0}\t{1},1".format(departamento, precio_base))

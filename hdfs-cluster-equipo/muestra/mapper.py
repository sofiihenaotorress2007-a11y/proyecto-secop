#!/usr/bin/env python3
# Lee secop_sample.csv (SECOP II - Procesos de Contratacion, 59 columnas) y
# emite: departamento_entidad <tab> precio_base
#
# Usa csv.reader en vez de linea.split(","): varios campos de texto libre
# (nombre_del_procedimiento, descripci_n_del_procedimiento) traen comas
# dentro de comillas, y un split ingenuo correria las columnas.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta (llegaron en 3.6).
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "entidad":
        continue                      # salta encabezado y lineas vacias
    if len(campos) < 21:
        continue                      # linea incompleta (menos columnas de las esperadas)
    departamento, precio_base = campos[2], campos[20]
    try:
        precio_base = float(precio_base)
    except ValueError:
        continue
    print("{0}\t{1}".format(departamento, precio_base))

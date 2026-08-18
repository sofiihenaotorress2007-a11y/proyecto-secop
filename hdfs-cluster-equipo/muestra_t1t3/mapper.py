#!/usr/bin/env python3
# Lee secop_sample_periodo2.csv (SECOP II - Contratos Electronicos, 15
# columnas, el dataset oficial de docs/ficha_tecnica.md y
# docs/proyeccion_almacenamiento.md) y emite:
# departamento <tab> valor_contrato
#
# Usa csv.reader porque varios campos de texto libre (objeto_contrato,
# descripcion_proceso, justificacion_modalidad, observaciones) pueden
# traer comas dentro de comillas.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta (llegaron en 3.6).
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "id_contrato":
        continue                      # salta encabezado y lineas vacias
    if len(campos) < 15:
        continue                      # linea incompleta
    departamento, valor_contrato = campos[8], campos[6]
    try:
        valor_contrato = float(valor_contrato)
    except ValueError:
        continue
    print("{0}\t{1}".format(departamento, valor_contrato))

#!/usr/bin/env python3
# Recibe pares departamento_entidad <tab> precio_base ordenados por clave
# (Hadoop ordena antes de entregar al reducer) y promedia precio_base por
# departamento.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta (llegaron en 3.6).
import sys

departamento_actual, suma, conteo = None, 0.0, 0
for linea in sys.stdin:
    departamento, precio_base = linea.strip().split("\t")
    precio_base = float(precio_base)
    if departamento != departamento_actual and departamento_actual is not None:
        print("{0}\t{1:.2f}".format(departamento_actual, suma / conteo))
        suma, conteo = 0.0, 0
    departamento_actual = departamento
    suma += precio_base
    conteo += 1
if departamento_actual is not None:
    print("{0}\t{1:.2f}".format(departamento_actual, suma / conteo))

#!/usr/bin/env python3
# Suma final de precio_base por modalidad_de_contratacion. Misma logica que
# combiner3.py (la reduccion final de una suma es otra suma), corra o no
# haya corrido el combinador antes.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta.
import sys

modalidad_actual, suma = None, 0.0
for linea in sys.stdin:
    modalidad, precio_base = linea.strip().split("\t")
    precio_base = float(precio_base)
    if modalidad != modalidad_actual and modalidad_actual is not None:
        print("{0}\t{1:.2f}".format(modalidad_actual, suma))
        suma = 0.0
    modalidad_actual = modalidad
    suma += precio_base
if modalidad_actual is not None:
    print("{0}\t{1:.2f}".format(modalidad_actual, suma))

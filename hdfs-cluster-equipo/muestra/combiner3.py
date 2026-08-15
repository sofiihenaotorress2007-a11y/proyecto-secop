#!/usr/bin/env python3
# Suma parcial de precio_base por modalidad_de_contratacion. Como la
# agregacion final es una suma (no un promedio), la suma de sumas parciales
# sigue siendo correcta sin importar cuantas veces corra el combinador, y
# sin necesidad de cargar un conteo aparte.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta.
import sys

modalidad_actual, suma = None, 0.0
for linea in sys.stdin:
    modalidad, precio_base = linea.strip().split("\t")
    precio_base = float(precio_base)
    if modalidad != modalidad_actual and modalidad_actual is not None:
        print("{0}\t{1}".format(modalidad_actual, suma))
        suma = 0.0
    modalidad_actual = modalidad
    suma += precio_base
if modalidad_actual is not None:
    print("{0}\t{1}".format(modalidad_actual, suma))

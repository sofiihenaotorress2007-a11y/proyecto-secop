#!/usr/bin/env python3
# Recibe departamento_entidad <tab> suma,conteo (el combinador ya sumo
# localmente; sin combinador, llegarian pares precio_base,1 individuales,
# que este reductor tambien sabe sumar porque el formato es el mismo).
# Suma las sumas, suma los conteos, y solo entonces divide.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta.
import sys

departamento_actual, suma, conteo = None, 0.0, 0
for linea in sys.stdin:
    departamento, valor = linea.strip().split("\t")
    sub_suma, sub_conteo = valor.split(",")
    sub_suma, sub_conteo = float(sub_suma), int(sub_conteo)
    if departamento != departamento_actual and departamento_actual is not None:
        print("{0}\t{1:.2f}".format(departamento_actual, suma / conteo))
        suma, conteo = 0.0, 0
    departamento_actual = departamento
    suma += sub_suma
    conteo += sub_conteo
if departamento_actual is not None:
    print("{0}\t{1:.2f}".format(departamento_actual, suma / conteo))

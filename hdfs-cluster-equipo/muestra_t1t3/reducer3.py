#!/usr/bin/env python3
# Suma final por modalidad_contratacion: suma las sumas parciales que
# llegan de todos los nodos de mapa, hayan pasado o no por el
# combinador.
import sys


def emitir(clave, suma):
    if clave is not None:
        print("{0}\t{1}".format(clave, suma))


clave_actual = None
suma = 0.0

for linea in sys.stdin:
    try:
        clave, valor = linea.rstrip("\n").split("\t")
        valor = float(valor)
    except ValueError:
        continue
    if clave == clave_actual:
        suma += valor
    else:
        emitir(clave_actual, suma)
        clave_actual = clave
        suma = valor

emitir(clave_actual, suma)

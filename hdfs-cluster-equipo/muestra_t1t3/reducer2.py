#!/usr/bin/env python3
# Nivel 2, con combinador: suma las sumas parciales y los conteos
# parciales que llegan de todos los nodos de mapa (hayan pasado o no por
# el combinador) y solo entonces divide, produciendo el promedio final de
# valor_contrato por departamento.
import sys


def emitir(clave, suma, conteo):
    if clave is not None and conteo > 0:
        print("{0}\t{1}".format(clave, suma / conteo))


clave_actual = None
suma = 0.0
conteo = 0

for linea in sys.stdin:
    try:
        clave, resto = linea.rstrip("\n").split("\t")
        valor_str, conteo_str = resto.split(",")
        valor = float(valor_str)
        c = int(conteo_str)
    except ValueError:
        continue
    if clave == clave_actual:
        suma += valor
        conteo += c
    else:
        emitir(clave_actual, suma, conteo)
        clave_actual = clave
        suma = valor
        conteo = c

emitir(clave_actual, suma, conteo)

#!/usr/bin/env python3
# Nivel 1, sin combinador: recibe departamento <tab> valor_contrato (un
# par por fila de entrada) y emite el promedio de valor_contrato por
# departamento.
import sys


def emitir(clave, suma, conteo):
    if clave is not None and conteo > 0:
        print("{0}\t{1}".format(clave, suma / conteo))


clave_actual = None
suma = 0.0
conteo = 0

for linea in sys.stdin:
    try:
        clave, valor = linea.rstrip("\n").split("\t")
        valor = float(valor)
    except ValueError:
        continue
    if clave == clave_actual:
        suma += valor
        conteo += 1
    else:
        emitir(clave_actual, suma, conteo)
        clave_actual = clave
        suma = valor
        conteo = 1

emitir(clave_actual, suma, conteo)

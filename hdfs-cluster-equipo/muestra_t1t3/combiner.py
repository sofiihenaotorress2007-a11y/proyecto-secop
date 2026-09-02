#!/usr/bin/env python3
# Agrega sumas parciales y conteos parciales por clave, dentro de un
# mismo nodo de mapa, antes de que crucen la mezcla. Nunca promedia aqui:
# el combinador puede correr 0, 1 o varias veces, y su entrada y su
# salida comparten el mismo formato (suma,conteo) para que eso sea
# seguro.
import sys


def emitir(clave, suma, conteo):
    if clave is not None:
        print("{0}\t{1},{2}".format(clave, suma, conteo))


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

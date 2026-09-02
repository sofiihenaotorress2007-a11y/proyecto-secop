#!/usr/bin/env python3
# Agrega localmente antes de la mezcla: recibe departamento_entidad <tab>
# precio_base,conteo (conteo casi siempre 1, salvo que el propio combinador
# ya se haya ejecutado antes sobre ese grupo) y emite suma parcial y
# conteo por departamento. NO promedia: Hadoop puede correr el combinador
# cero, una o varias veces, asi que su salida debe tener el mismo formato
# que su entrada (suma,conteo entran, suma,conteo salen).
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
        print("{0}\t{1},{2}".format(departamento_actual, suma, conteo))
        suma, conteo = 0.0, 0
    departamento_actual = departamento
    suma += sub_suma
    conteo += sub_conteo
if departamento_actual is not None:
    print("{0}\t{1},{2}".format(departamento_actual, suma, conteo))

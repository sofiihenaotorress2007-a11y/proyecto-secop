#!/usr/bin/env python3
# Pregunta de negocio (Nivel 3): que modalidad de contratacion concentra
# mas valor de contrato en total? Clave: modalidad_contratacion (columna
# 3). A diferencia del promedio, la suma no necesita un conteo
# acompanando al valor: la suma de sumas parciales sigue siendo la suma
# total sin importar cuantas veces corra el combinador, por eso
# mapper3.py emite el valor crudo directamente.
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "id_contrato":
        continue
    if len(campos) < 15:
        continue
    modalidad, valor_contrato = campos[3], campos[6]
    try:
        valor_contrato = float(valor_contrato)
    except ValueError:
        continue
    print("{0}\t{1}".format(modalidad, valor_contrato))

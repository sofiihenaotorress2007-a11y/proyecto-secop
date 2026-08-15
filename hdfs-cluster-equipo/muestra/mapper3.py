#!/usr/bin/env python3
# Nivel 3 - agregacion propia: precio_base TOTAL (suma, no promedio) por
# modalidad_de_contratacion. Pregunta de negocio: que modalidad de
# contratacion concentra mas presupuesto base ofertado en total.
# Emite: modalidad_de_contratacion <tab> precio_base
#
# A diferencia del promedio (nivel 1/2), la suma no necesita cargar un
# conteo junto al valor: la suma de sumas parciales sigue siendo la suma
# total, asi que el mapper puede emitir el valor crudo directamente y el
# combinador/reductor comparten el mismo formato de entrada y salida.
#
# Sin f-strings a proposito: el nodemanager del cluster corre Python 3.5
# (Debian stretch, EOL), que no las soporta.
import csv
import sys

lector = csv.reader(sys.stdin)
for campos in lector:
    if not campos or campos[0] == "entidad":
        continue
    if len(campos) < 22:
        continue
    modalidad, precio_base = campos[21], campos[20]
    try:
        precio_base = float(precio_base)
    except ValueError:
        continue
    print("{0}\t{1}".format(modalidad, precio_base))

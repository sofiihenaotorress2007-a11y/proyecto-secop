# Práctica Sesión 3 · Clúster HDFS

Clúster HDFS local (1 namenode + 3 datanodes) usado para generar la evidencia
práctica detrás de la decisión de tamaño de bloque documentada en
`docs/proyeccion_almacenamiento.md`, sección "Nivel 3 — Decisión de tamaño de bloque".

Incluye dos configuraciones:
- `hadoop.env` — Nivel 1 (default HDFS: bloque 128 MB, factor de réplica 3)
- `hadoop_nivel2.env` — Nivel 2 (experimento: bloque 8 MB, factor de réplica 2)

## Cómo levantar el clúster

```bash
docker compose up -d
```

El flag `-d` lo corre en segundo plano (así puedes seguir usando la misma
terminal).

Espera unos 30-60 segundos a que los 4 contenedores terminen de arrancar.

## Verifica que los 4 nodos están corriendo

```bash
docker compose ps
```

Deberías ver `hdfs-namenode`, `hdfs-datanode1`, `hdfs-datanode2`,
`hdfs-datanode3`, todos con estado `Up` (y luego `healthy`).

## Abre la interfaz web del namenode

```
http://localhost:9870
```

Ahí puedes ver, sin usar ningún comando: el número de datanodes activos,
la capacidad total, y (en la pestaña "Datanodes") el estado de cada nodo.

## Carga un archivo al clúster

Usa cualquier muestra del dataset del equipo (por ejemplo, un CSV de SECOP II)
como archivo de prueba.

**1.** Copia el archivo dentro del contenedor del namenode:
```bash
docker cp tu_archivo.csv hdfs-namenode:/tmp/secop.csv
```
(corre este comando desde la carpeta donde esté el archivo, o usa la ruta completa)

**2.** Entra a una terminal dentro del namenode:
```bash
docker exec -it hdfs-namenode bash
```

**3.** Dentro de esa terminal (ya no es tu terminal de Windows, es la del
contenedor), crea una carpeta en HDFS y sube el archivo:
```bash
hdfs dfs -mkdir -p /practica
hdfs dfs -put /tmp/secop.csv /practica/secop.csv
```

**4.** Verifica que quedó ahí:
```bash
hdfs dfs -ls /practica
```

**5.** Inspecciona los bloques y en qué nodos están las réplicas:
```bash
hdfs fsck /practica/secop.csv -files -blocks -locations
```
Esto muestra cuántos bloques tiene el archivo y en qué datanodes vive cada
réplica — la evidencia real detrás de la tabla teórica de la guía.

**6.** Sal de la terminal del contenedor:
```bash
exit
```

## Simula la caída de un nodo

Con el archivo ya cargado y replicado, apaga uno de los datanodes:
```bash
docker stop hdfs-datanode2
```

Vuelve a la interfaz web (`http://localhost:9870` → pestaña Datanodes) y
confirma que aparece como caído, pero el archivo se sigue leyendo:
```bash
docker exec -it hdfs-namenode hdfs dfs -cat /practica/secop.csv
```
(o vuelve a correr el `fsck` del paso 5 y observa cómo cambia el conteo de
"Under-replicated blocks")

## Para volver a levantar el nodo caído

```bash
docker start hdfs-datanode2
```

## Para reproducir el experimento del Nivel 2 (bloque 8 MB, réplica 2)

```bash
docker compose down -v
```
Reemplaza el contenido de `hadoop.env` por el de `hadoop_nivel2.env` (o
renombra el archivo), y vuelve a levantar:
```bash
docker compose up -d
```
El `-v` es obligatorio: HDFS no permite cambiar el tamaño de bloque de un
sistema de archivos que ya tiene datos.

## Para apagar todo el clúster

```bash
docker compose down
```

Para borrar también los datos guardados (reinicio completo):
```bash
docker compose down -v
```

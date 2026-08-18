# Proyecto · SECOP II — Contratos Electrónicos

Proyecto del curso IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean.
Fuente de datos: **SECOP II — Contratos Electrónicos**, publicada por la Agencia Nacional de Contratación Pública (Colombia Compra Eficiente) en datos.gov.co.

---

## Requisitos previos

Lo que debe estar instalado antes de empezar:

- Git
- Docker Desktop (incluye Docker Compose)

No se requiere instalar Python, pandas, PostgreSQL ni ninguna librería en el equipo anfitrión: todo corre dentro de los contenedores.

**Ruta de infraestructura usada:** A · Docker local

---

## Cómo levantar el entorno

Pasos exactos, del clon a un entorno corriendo:

```
# 1. Clonar
git clone https://github.com/sofiihenaotorress2007-a11y/proyecto-secop.git
cd proyecto-secop

# 2. Configurar variables de entorno
cp .env.example .env
# los valores de ejemplo funcionan para uso local; edítelos si lo requiere

# 3. Levantar
docker compose up
```

La primera vez tarda varios minutos: descarga las imágenes de Jupyter y PostgreSQL, e instala las dependencias ancladas en `requirements.txt`.

---

## Cómo saber que quedó bien

Qué debe ver cuando todo funciona:

- La terminal muestra `Jupyter Server ... is running at: http://localhost:8888/lab`
- Jupyter está disponible en http://localhost:8888 sin pedir token
- El cuaderno `notebooks/00_verificacion.ipynb` corre completo (Run → Run All Cells) sin errores de importación ni discrepancias de versión
- La última celda del cuaderno imprime `Conexion exitosa a PostgreSQL`, confirmando que el servicio `jupyter` alcanza al servicio `db` por la red interna de Docker Compose

---

## Cómo se apaga

```
docker compose down
```

Para además borrar los datos persistidos de PostgreSQL (reinicio completo):

```
docker compose down -v
```

---

## Estructura del proyecto

```
proyecto-secop/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── .env.example          # claves sin valores, como referencia
├── data/raw/              # datos, NO versionados
├── notebooks/
│   └── 00_verificacion.ipynb
├── src/
├── docs/
│   ├── ficha_tecnica.md              # T1
│   ├── decision_frontera_contenedor.md
│   ├── proyeccion_almacenamiento.md  # T3
│   ├── reto_negocio.md
│   ├── justificacion_fuente_equipo.md
│   ├── glosario.md
│   └── guia_incorporacion.md
└── hdfs-cluster-equipo/               # cluster HDFS+YARN (sesiones 3-4)
    ├── docker-compose.yml            # namenode, datanodes, YARN
    ├── EVIDENCIA_T4.md                # T4: MapReduce, combinador, contadores
    ├── muestra/                       # mapper/reducer/combiner (evidencia original)
    └── muestra_t1t3/                  # mismo, adaptado al dataset oficial de T1/T3
```

---

## Si algo falla

| Problema | Solución |
|---|---|
| Puerto 8888 ocupado | Cambie el mapeo en `docker-compose.yml` a `"8889:8888"` y acceda por `http://localhost:8889` |
| `failed to resolve reference` al hacer `docker compose up` | El tag de una imagen no existe en el registro. Ver causa raíz documentada en `docs/decision_frontera_contenedor.md` |
| La instalación se queda compilando una librería (ej. pandas) y falla | La versión anclada en `requirements.txt` no tiene paquete precompilado para la versión de Python de la imagen. Ver `docs/decision_frontera_contenedor.md` |
| El navegador dice "Kernel does not exist" al abrir un notebook | Quedó una pestaña vieja de una sesión anterior de Docker. Cierre la pestaña, refresque, y abra `http://localhost:8888` de nuevo |

Contacto del responsable del repositorio: Ana Sofía Henao Torres (usuario de GitHub: sofiihenaotorress2007-a11y).

---

## Guía de incorporación

Ver `docs/guia_incorporacion.md` — guía de una página para que un integrante nuevo del equipo tenga el proyecto corriendo en su primer día sin depender de nadie más, incluyendo los tres fallos reales encontrados durante la construcción de este repositorio.

---

## Declaración de uso de asistentes de inteligencia artificial

- **Herramienta usada:** Claude (Anthropic)
- **En qué parte:** diseño de la estructura de carpetas, redacción inicial de `docker-compose.yml` y `requirements.txt`, diagnóstico y corrección de tres fallos reales de compatibilidad de versiones con Python 3.13 (detallados en `docs/decision_frontera_contenedor.md`), y redacción de la documentación (README, ficha técnica, decisión de frontera del contenedor, guía de incorporación).
- **Qué verifiqué contra ejecución real:** confirmé que el compose levanta el entorno desde un estado limpio ejecutando `docker compose down -v` (que borra también los datos de PostgreSQL) seguido de `docker compose up` en mi propio equipo, y corriendo el cuaderno de verificación completo, incluida la celda de conexión a PostgreSQL, con resultado exitoso.

---

## Lista de verificación antes de entregar

- [x] `.gitignore` escrito antes del primer commit; no hay datos ni credenciales en la historia
- [x] `requirements.txt` con todas las versiones ancladas con doble igual
- [x] `docker-compose.yml` con dos servicios y versiones ancladas
- [x] Cuaderno de verificación ejecutado, con salidas visibles
- [x] Ficha T1 versionada en `docs/`
- [x] Varios commits con mensajes que explican qué cambió
- [x] **Prueba del clon limpio:** cloné en una carpeta nueva y levantó sin que yo tocara nada
- [x] Repositorio público

---

## Fuente del proyecto

Ver `docs/ficha_tecnica.md` para el detalle completo de origen, licencia, mediciones de volumen y cálculo del umbral de saturación de esta fuente.

---

*IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean. README basado en la plantilla T2, versión `S02_P6_v1`.*

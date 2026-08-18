FROM bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8

# El nodemanager corre sobre Debian 9 "stretch", que llego a EOL y ya no
# esta servido en deb.debian.org: sin este cambio, apt-get update falla
# con 404 antes de poder instalar nada.
RUN sed -i \
      -e 's|deb.debian.org/debian|archive.debian.org/debian|g' \
      -e 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' \
      -e '/stretch-updates/d' \
      /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

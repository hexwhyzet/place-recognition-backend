FROM postgres:16.1

RUN apt-get update \
    && apt-get install wget -y \
    && apt-get install postgresql-16-postgis-3 -y \
    && apt-get install postgis -y

COPY ../configs/postgres/load-extensions.sh /docker-entrypoint-initdb.d/
FROM clickhouse/clickhouse-server

COPY ../configs/clickhouse/config.xml /etc/clickhouse-server/config.d/
COPY ../configs/clickhouse/users.xml /etc/clickhouse-server/users.d/
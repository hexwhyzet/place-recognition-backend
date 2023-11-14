--liquibase formatted sql
--changeset kabakov-ivan:create-request-table
CREATE TABLE IF NOT EXISTS logs.request
(
    ID           UInt128 PRIMARY KEY,
    Timestamp    DateTime,
    IPv4         IPv4,
    RequestHeaders Map(String, String),
    RequestBody  String,
    RequestURL   String,
    HTTPMethod Enum('GET' = 1, 'HEAD' = 2, 'POST' = 3, 'PUT' = 4, 'DELETE' = 5, 'CONNECT' = 6, 'OPTIONS' = 7, 'TRACE' = 8, 'PATCH' = 9),
    UserAgent    String,
    ResponseHeaders Map(String, String),
    ResponseBody String,
    Status       UInt16,
    ResponseTime Float64
) ENGINE = MergeTree
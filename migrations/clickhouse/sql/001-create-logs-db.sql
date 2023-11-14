--liquibase formatted sql
--changeset kabakov-ivan:create-logs-database
CREATE DATABASE IF NOT EXISTS logs;
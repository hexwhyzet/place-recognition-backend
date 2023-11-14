--liquibase formatted sql
--changeset kabakov-ivan:create-request-table
CREATE TABLE IF NOT EXISTS logs.recognition
(
    RequestID          UInt128 PRIMARY KEY,
    Timestamp          DateTime,
    ResultBuildingID   UInt64,
    ClosestBuildingIDs Array(UInt64),
    ClosestSize        UInt32,
    ReleaseName        String,
    Descriptor         Array(Float64),
    DescriptorSize     UInt32,
    Coordinates        Point,
    Model              String,
    Predictor          String,
    ShowResult         Boolean
) ENGINE = MergeTree
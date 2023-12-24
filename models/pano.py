from datetime import datetime as dt
from enum import Enum as PythonEnum
from typing import Optional, List, Any

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from pydantic.fields import ModelField
from sqlalchemy import Column, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from libs.coordinates import Coordinates, CoordinateSystem, MAIN_COORDINATE_SYSTEM
from models.base import BaseSQLModel


class PanoSource(PythonEnum):
    GOOGLE = 1
    YANDEX = 2


class WKBElementSerializable:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val, field: ModelField):
        point = to_shape(val)
        latitude, longitude = Coordinates.convert(
            point.x, point.y,
            from_system=MAIN_COORDINATE_SYSTEM,
            to_system=CoordinateSystem.ELLIPSOID)
        return {'latitude': latitude, 'longitude': longitude}


class PanoBase(SQLModel):
    width: int = Field(nullable=False)
    height: int = Field(nullable=False)
    zoom: int = Field(nullable=True)


class Pano(PanoBase, BaseSQLModel, table=True):
    pano_meta_id: Optional[int] = Field(
        foreign_key="pano_meta.id",
        nullable=False,
    )
    pano_meta: "PanoMeta" = Relationship(
        back_populates="panos"
    )


class PanoRead(PanoBase):
    pass


class PanoMetaBase(SQLModel):
    source: PanoSource = Field(
        sa_column=Column(
            SQLAlchemyEnum(PanoSource),
            nullable=False,
        )
    )
    primary_id: str = Field(nullable=False)
    secondary_id: str = Field(nullable=True, default=None)
    datetime: dt = Field(nullable=False)
    direction: float = Field(nullable=False)


class PanoMeta(PanoMetaBase, BaseSQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("source", "primary_id", name="unique_pano_id_for_source"),
    )
    coordinates: Any = Field(
        sa_column=Column(
            Geometry('POINT'),
            nullable=False,
        )
    )
    panos: List["Pano"] = Relationship(
        back_populates="pano_meta",
    )


class PanoMetaRead(PanoMetaBase):
    coordinates: WKBElementSerializable = None
    panos: List["PanoRead"] = None

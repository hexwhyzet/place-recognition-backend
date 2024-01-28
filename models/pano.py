from datetime import datetime as dt
from enum import Enum as PythonEnum
from typing import Optional, List, Any

from geoalchemy2 import Geometry
from sqlalchemy import Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from models.base import BaseSQLModel, BaseSQLEnum
from models.common import CoordinatesSerializable


class Pano(BaseSQLModel, table=True):
    meta_id: Optional[int] = Field(foreign_key="pano_meta.id", nullable=False)
    meta: "PanoMeta" = Relationship(back_populates="pano")

    spec_id: Optional[int] = Field(foreign_key="pano_spec.id", nullable=True, default=None)
    spec: Optional["PanoSpec"] = Relationship(back_populates="pano")


class PanoSource(PythonEnum):
    GOOGLE = 1
    YANDEX = 2


class PanoMetaBase(SQLModel):
    __table_args__ = (
        UniqueConstraint("source_image_id", "source", name="unique_pano_id_for_source"),
    )
    source_image_id: str = Field(nullable=False)
    source_pano_id: str = Field(nullable=True, default=None)
    source: PanoSource = Field(
        sa_column=Column(
            BaseSQLEnum(PanoSource),
            nullable=False,
        )
    )


class PanoMeta(PanoMetaBase, BaseSQLModel, table=True):
    pano: Pano = Relationship(
        sa_relationship_kwargs={'uselist': False},
        back_populates="meta",
    )


class PanoMetaRead(PanoMetaBase):
    pass


class PanoSizeBase(SQLModel):
    zoom: int = Field(nullable=False)
    width: int = Field(nullable=False)
    height: int = Field(nullable=False)


class PanoSize(PanoSizeBase, BaseSQLModel, table=True):
    pano_spec_id: Optional[int] = Field(
        foreign_key="pano_spec.id",
        nullable=False,
    )
    pano_spec: "PanoSpec" = Relationship(
        sa_relationship_kwargs={'uselist': False},
        back_populates="sizes"
    )


class PanoSizeRead(PanoSizeBase):
    pass


class PanoSpecBase(SQLModel):
    datetime: dt = Field(nullable=True)
    direction: float = Field(nullable=False)
    copyright: str = Field(nullable=False)


class PanoSpec(PanoSpecBase, BaseSQLModel, table=True):
    coordinates: Any = Field(
        sa_column=Column(
            Geometry('POINT'),
            nullable=False,
        )
    )
    sizes: List["PanoSize"] = Relationship(
        back_populates="pano_spec",
    )
    pano: Pano = Relationship(back_populates="spec")


class PanoSpecRead(PanoMetaBase):
    coordinates: CoordinatesSerializable = None
    panos: List["PanoSizeRead"] = None

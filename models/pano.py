from enum import Enum as PythonEnum
from typing import Optional

from sqlalchemy import Column, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlmodel import Field, SQLModel

from libs.coordinates import Coordinates
from models.base import BaseSQLModel


class PanoSource(PythonEnum):
    GOOGLE = 1
    YANDEX = 2


class Pano(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("source", "primary_id", name="your_unique_constraint_name"),
    )

    source: PanoSource = Field(
        sa_column=Column(
            SQLAlchemyEnum(PanoSource),
            nullable=False,
        )
    )
    primary_id: str = Field()
    secondary_id: str = Field()

    coordinates: Coordinates = None

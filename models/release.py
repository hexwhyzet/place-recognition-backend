from typing import Optional, Any, List

from geoalchemy2 import Geometry
from sqlmodel import Field, ARRAY, Column, Float, Relationship

from models.base import BaseSQLModel
from models.link import RecognitionReleaseItemLink


class Release(BaseSQLModel, table=True):
    name: str = Field(nullable=False, unique=True)
    items: List['ReleaseItem'] = Relationship(
        back_populates='release'
    )


class ReleaseItem(BaseSQLModel, table=True):
    release_id: Optional[int] = Field(foreign_key='release.id', nullable=False)
    release: Optional[Release] = Relationship(
        back_populates='items',
    )
    building_id: Optional[int] = Field(foreign_key='building.id', nullable=False)
    image_url: Optional[str] = Field(nullable=False)
    location: Any = Field(
        sa_column=Column(
            Geometry('POINT'),
            nullable=False,
        ),
    )
    descriptor: List[float] = Field(
        sa_column=Column(
            ARRAY(Float),
            nullable=False,
        ),
    )
    recognitions: List["Recognition"] = Relationship(back_populates="release_items",
                                                     link_model=RecognitionReleaseItemLink)

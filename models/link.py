from typing import Optional

from sqlmodel import Field

from models.base import BaseSQLModel


class RecognitionReleaseItemLink(BaseSQLModel, table=True):
    recognition_id: Optional[int] = Field(
        default=None, foreign_key="recognition.id"
    )
    release_item_id: Optional[int] = Field(
        default=None, foreign_key="release_item.id"
    )
    priority: int = Field(nullable=False)


class BuildingMetroLink(BaseSQLModel, table=True):
    building_id: Optional[int] = Field(
        default=None, foreign_key="building.id"
    )
    metro_station_id: Optional[int] = Field(
        default=None, foreign_key="metro_station.id"
    )
    priority: int = Field(nullable=False)

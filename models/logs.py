from datetime import datetime
from enum import Enum
from typing import Optional, List, Any

from geoalchemy2 import Geometry
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import HSTORE, UUID
from sqlalchemy.types import BigInteger
from sqlmodel import Field, ARRAY, Column, Float
from sqlmodel import Relationship

from models.release import ReleaseItem
from models.base import TableNameSQLMode
from models.geo import Building
from models.link import RecognitionReleaseItemLink


class HTTPMethod(str, Enum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'


class Request(TableNameSQLMode, table=True):
    id: Any = Field(sa_column=Column(UUID(as_uuid=True), primary_key=True))
    timestamp: datetime = Field(nullable=False)
    ipv4: str = Field(nullable=False)
    request_headers: dict = Field(
        sa_column=Column(
            HSTORE,
            nullable=False,
        )
    )
    request_body: str = Field(nullable=False)
    request_url: str = Field(nullable=False)
    http_method: HTTPMethod = Field(
        sa_column=Column(
            SQLAlchemyEnum(HTTPMethod),
            nullable=False,
        )
    )
    user_agent: str = Field(nullable=False)
    response_headers: dict = Field(
        sa_column=Column(
            HSTORE,
            nullable=False,
        )
    )
    response_body: str = Field(nullable=True)
    status: int = Field(nullable=False)
    response_time: float = Field(nullable=False)


class Recognition(TableNameSQLMode, table=True):
    id: int = Field(
        sa_column=Column(
            BigInteger,
            primary_key=True,
            autoincrement=True,
        )
    )
    request_id: Any = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            nullable=False,
        )
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    result_building_id: Optional[int] = Field(foreign_key="building.id", nullable=True, default=None)
    result_building: Optional[Building] = Relationship(sa_relationship_kwargs={"cascade": "delete"})
    release_items: List[ReleaseItem] = Relationship(back_populates="recognitions",
                                                    link_model=RecognitionReleaseItemLink)
    closest_size: int = Field(nullable=False)
    release_name: str = Field(foreign_key="release.name", nullable=False)
    descriptor: List[float] = Field(
        sa_column=Column(
            ARRAY(Float),
            nullable=False,
        ),
    )
    descriptor_size: int = Field(nullable=False)
    coordinates: Any = Field(
        sa_column=Column(
            Geometry('POINT'),
            nullable=True,
        ),
    )
    model: str = Field(nullable=False)
    predictor: str = Field(nullable=False)
    debug_token: str = Field(nullable=True)

from typing import Optional, Any, List

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from shapely import MultiPolygon
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

from libs.coordinates import CoordinateSystem, Coordinates
from models.base import BaseSQLModel
from models.language import TextContent, TextContentRead
from models.link import BuildingMetroLink


class MetroLineBase(BaseSQLModel):
    name_id: Optional[int] = Field(foreign_key="text_content.id", nullable=False, exclude=True)
    stations: List["MetroStation"] = Relationship(back_populates="line")


class MetroLine(MetroLineBase, table=True):
    name: Optional[TextContent] = Relationship(sa_relationship_kwargs={"cascade": "delete"})
    stations: List["MetroStation"] = Relationship(back_populates="line")


class MetroLineRead(MetroLineBase):
    name: Optional[TextContentRead] = None


class MetroStationBase(BaseSQLModel):
    name_id: Optional[int] = Field(foreign_key="text_content.id", nullable=False, exclude=True)
    coordinates: Any = Field(
        sa_column=Column(
            Geometry('POINT'),
            nullable=False,
        ),
        exclude=True
    )
    line_id: int = Field(foreign_key="metro_line.id", default=None, exclude=True)


class MetroStation(MetroStationBase, table=True):
    name: Optional[TextContent] = Relationship(sa_relationship_kwargs={"cascade": "delete"})
    line: Optional[MetroLine] = Relationship(back_populates="stations")
    buildings: List["Building"] = Relationship(back_populates="metro_stations",
                                               link_model=BuildingMetroLink)


class MetroStationRead(MetroStationBase):
    name: Optional[TextContentRead] = None
    line: Optional[MetroLineRead] = None


class BuildingGroupBase(SQLModel):
    is_visible: Optional[bool] = Field(default=False, nullable=False, exclude=True)
    title_id: Optional[int] = Field(foreign_key="text_content.id", default=None, exclude=True)
    description_id: Optional[int] = Field(foreign_key="text_content.id", default=None, exclude=True)
    construction_year: Optional[int] = Field(default=None)
    image_url: Optional[str] = Field(default=None)


class BuildingGroup(BuildingGroupBase, BaseSQLModel, table=True):
    buildings: List["Building"] = Relationship(back_populates="group")
    title: Optional[TextContent] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BuildingGroup.title_id==TextContent.id",
            "lazy": "joined",
            "cascade": "delete"
        }
    )
    description: Optional[TextContent] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "BuildingGroup.description_id==TextContent.id",
            "lazy": "joined",
            "cascade": "delete"
        }
    )


class BuildingGroupRead(BuildingGroupBase):
    id: int
    title: Optional[TextContentRead] = None
    description: Optional[TextContentRead] = None


class GeoObject(SQLModel):
    geometry: Any = Field(
        sa_column=Column(
            Geometry('MULTIPOLYGON'),
            nullable=False,
        ),
        exclude=True
    )

    @property
    def geometry_shape(self) -> MultiPolygon:
        return to_shape(self.geometry)

    def set_geometry_shape(self, data):
        self.geometry = from_shape(data)

    def distance(self, other) -> float:
        return self.geometry_shape.distance(other)

    def intersects(self, other) -> bool:
        return self.geometry_shape.intersects(other)

    def intersection(self, other):
        return self.geometry_shape.intersection(other)

    def contains(self, other):
        return self.geometry_shape.contains(other)


class BuildingBase(GeoObject):
    group_id: Optional[int] = Field(foreign_key="building_group.id", nullable=False, exclude=True)
    address_id: Optional[int] = Field(foreign_key="text_content.id", default=None, exclude=True)


class Building(BuildingBase, BaseSQLModel, table=True):
    group: Optional[BuildingGroup] = Relationship(back_populates="buildings")
    address: Optional[TextContent] = Relationship(sa_relationship_kwargs={"cascade": "delete"})
    metro_stations: List[MetroStation] = Relationship(back_populates="buildings",
                                                      link_model=BuildingMetroLink)


class BuildingRead(BuildingBase):
    id: int
    address: Optional[TextContentRead] = None
    metro_stations: Optional[List[MetroStationRead]] = None


class BuildingReadWithGroup(BuildingRead):
    group: Optional["BuildingGroupRead"] = None


class Area(GeoObject):
    @staticmethod
    def from_coordinates(coordinate_system: CoordinateSystem, coordinates):
        parsed_coords = [
            Coordinates.convert(
                coordinate['lat'],
                coordinate['lng'],
                coordinate_system,
                CoordinateSystem.PROJECTION
            ) for coordinate in coordinates
        ]
        geometry = MultiPolygon([[parsed_coords, []]])
        area = Area()
        area.set_geometry_shape(geometry)
        return area

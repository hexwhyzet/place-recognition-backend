from enum import Enum
from typing import Union

from pydantic import BaseModel
from pyproj import Transformer
from shapely import Point


class CoordinateSystem(str, Enum):
    ELLIPSOID = 'epsg:4326'
    PROJECTION = 'epsg:3857'


MAIN_COORDINATE_SYSTEM = CoordinateSystem.PROJECTION


class Coordinates(BaseModel):
    latitude: float
    longitude: float
    system: CoordinateSystem

    def __init__(self, latitude: float, longitude: float, system: Union[CoordinateSystem, str]):
        if isinstance(system, str):
            system = CoordinateSystem(system)
        super().__init__(latitude=latitude, longitude=longitude, system=system)
        self.latitude, self.longitude, self.system = latitude, longitude, system

    @staticmethod
    def convert(latitude: float, longitude: float, from_system: CoordinateSystem, to_system: CoordinateSystem) -> tuple:
        transformer = Transformer.from_crs(from_system.value, to_system.value)
        return transformer.transform(latitude, longitude)

    def converted(self, system: CoordinateSystem) -> 'Coordinates':
        converted_latitude, converted_longitude = self.convert(self.latitude, self.longitude, self.system, system)
        return Coordinates(converted_latitude, converted_longitude, system)

    def point(self, system: CoordinateSystem) -> Point:
        converted_coordinates = self.converted(system)
        return Point(converted_coordinates.latitude, converted_coordinates.longitude)

    def shift(self, latitude: float, longitude: float, system: CoordinateSystem):
        converted_coordinates = self.converted(system)
        return Coordinates(converted_coordinates.latitude + latitude,
                           converted_coordinates.longitude + longitude,
                           system)

from geoalchemy2.shape import to_shape
from pydantic.fields import ModelField

from libs.coordinates import Coordinates, MAIN_COORDINATE_SYSTEM, CoordinateSystem


class CoordinatesSerializable:
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

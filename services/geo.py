from typing import Union

from shapely import Point
from sqlmodel import Session, select

from models.base import BaseSQLModel
from models.geo import GeoObject, MetroStation


def select_closest_geo_objects(session: Session, geo_object: Union[GeoObject, BaseSQLModel], limit: int):
    geo_object_type = type(geo_object)
    centroid = geo_object.geometry_shape.centroid
    statement = select(geo_object_type) \
        .where(geo_object_type.id != geo_object.id) \
        .order_by(geo_object_type.geometry.distance_box(str(centroid))) \
        .limit(limit)
    return session.exec(statement).all()


def select_closest_metro_stations(session: Session, geo_object: Union[GeoObject, BaseSQLModel], limit: int):
    centroid = geo_object.geometry_shape.centroid
    statement = select(MetroStation) \
        .order_by(MetroStation.coordinates.distance_box(str(centroid))) \
        .limit(limit)
    return session.exec(statement).all()


def select_closest_geo_objects_to_point(session: Session, geo_object_type: type[GeoObject, BaseSQLModel], point: Point,
                                        limit: int):
    statement = select(geo_object_type) \
        .order_by(geo_object_type.geometry.distance_box(str(point))) \
        .limit(limit)
    return session.exec(statement).all()


def selected_geo_object_exists(session: Session, geo_object_type: type[GeoObject, BaseSQLModel], geo_object_id: int):
    return session.execute(select(geo_object_type).where(geo_object_type.id == geo_object_id)).first() is not None


def select_geo_object_by_id(session: Session, geo_object_type: type[GeoObject, BaseSQLModel], geo_object_id: int):
    return session.get(geo_object_type, geo_object_id)

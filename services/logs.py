import uuid
from typing import List, Union

from geoalchemy2.shape import from_shape
from shapely import Point
from sqlmodel import Session, select

from models import ReleaseItem
from models.link import RecognitionReleaseItemLink
from models.logs import HTTPMethod, Request, Recognition


def create_request(session: Session,
                   id: uuid.UUID,
                   timestamp: int,
                   ipv4: str,
                   request_headers: dict,
                   request_body: bytes,
                   request_url: str,
                   http_method: HTTPMethod,
                   user_agent: str,
                   response_headers: dict,
                   response_body: bytes,
                   status: int,
                   response_time: float):
    session.add(Request(
        id=id,
        timestamp=timestamp,
        ipv4=ipv4,
        request_headers=request_headers,
        request_body=request_body,
        request_url=request_url,
        http_method=http_method,
        user_agent=user_agent,
        response_headers=response_headers,
        response_body=response_body,
        status=status,
        response_time=response_time,
    ))
    session.commit()


def create_recognition(session: Session,
                       request_id: uuid.UUID,
                       timestamp: int,
                       result_building_id: int,
                       release_items: List[ReleaseItem],
                       closest_size: int,
                       release_name: str,
                       descriptor: List[float],
                       descriptor_size: int,
                       coordinates: Union[Point, None],
                       model: str,
                       predictor: str,
                       debug_token: str):
    recognition = Recognition(
        request_id=request_id,
        timestamp=timestamp,
        result_building_id=result_building_id,
        closest_size=closest_size,
        release_name=release_name,
        descriptor=descriptor,
        descriptor_size=descriptor_size,
        coordinates=from_shape(coordinates) if coordinates is not None else None,
        model=model,
        predictor=predictor,
        debug_token=debug_token,
    )
    session.add(recognition)
    session.flush()
    for index, release_item in enumerate(release_items):
        link = RecognitionReleaseItemLink(
            recognition_id=recognition.id,
            release_item_id=release_item.id,
            building_id=release_item.building_id,
            priority=index,
        )
        session.add(link)
    session.commit()


def last_recognition(session: Session, debug_token: str) -> Recognition:
    query = select(Recognition).where(Recognition.debug_token == debug_token).order_by(Recognition.id.desc())
    return session.exec(query).first()


def get_request(session: Session, request_id):
    return session.get(Request, request_id)

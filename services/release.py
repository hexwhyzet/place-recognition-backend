from typing import List

from geoalchemy2.shape import from_shape, to_shape
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from shapely import Point
from sqlmodel import Session, select
from tqdm import tqdm

from libs.coordinates import Coordinates, CoordinateSystem
from models.release import Release, ReleaseItem

QDRANT_COORDINATES_SYSTEM = CoordinateSystem.ELLIPSOID


def create_release(session: Session, name: str) -> Release:
    release = Release(name=name)
    session.add(release)
    session.commit()
    return release


def create_release_item(release: Release, descriptor: List[float], coordinates: Coordinates,
                        building_id: int, image_url: str):
    release_item = ReleaseItem(
        release=release,
        building_id=building_id,
        image_url=image_url,
        location=from_shape(coordinates.point(QDRANT_COORDINATES_SYSTEM)),
        descriptor=descriptor,
    )
    return release_item


def export_release_item(item: ReleaseItem, client: QdrantClient, release: Release):
    upsert_vector_release_item(
        client=client,
        collection_name=release.name,
        vector=item.descriptor,
        point=to_shape(item.location),
        building_id=item.building_id,
        image_url=item.image_url,
        release_item_id=item.id,
    )


def export_release(client: QdrantClient, release: Release):
    for item in tqdm(release.items, desc=f"Exporting release \"{release.name}\""):
        export_release_item(item, client, release)


def create_vector_release(client: QdrantClient, collection_name: str, vector_size: int,
                          distance: Distance = Distance.EUCLID):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )


def upsert_vector_release_item(client: QdrantClient, collection_name: str, vector: List[float],
                               point: Point, building_id: int, image_url: str, release_item_id: int):
    client.upsert(
        collection_name=collection_name,
        wait=True,
        points=[
            PointStruct(
                id=release_item_id,
                vector=vector,
                payload={
                    "locations": [{"lon": point.x, "lat": point.y}],
                    "building_id": building_id,
                    "image_url": image_url
                },
            ),
        ]
    )


def search_vector_release_item(client: QdrantClient, collection_name: str, vector: List[float], limit: int):
    return client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=limit
    )


def release_exists(session: Session, release_name: str):
    return session.exec(select(Release.name == release_name)).first() is not None

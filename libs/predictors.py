import dataclasses
from typing import List

from qdrant_client import QdrantClient
from sqlmodel import Session

from models import ReleaseItem
from services.release import search_vector_release_item


@dataclasses.dataclass
class Prediction:
    @property
    def answer(self) -> ReleaseItem:
        return self.closest[0]

    closest: List[ReleaseItem]


class PredictorBase:
    def __init__(self, qdrant_client: QdrantClient, release_name: str, limit: int = 15):
        self.release_name = release_name
        self.qdrant_client = qdrant_client
        self.limit = limit

    def predict(self, session: Session, vector: List[float]) -> Prediction:
        raise NotImplementedError


class PredictByClosestDescriptor(PredictorBase):
    def predict(self, session: Session, vector: List[float]) -> Prediction:
        n_closest = search_vector_release_item(
            client=self.qdrant_client,
            collection_name=self.release_name,
            vector=vector,
            limit=self.limit
        )
        return Prediction(closest=[session.get(ReleaseItem, scored_point.id) for scored_point in n_closest])

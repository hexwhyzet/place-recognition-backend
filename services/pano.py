from models.pano import PanoSource, PanoMeta
from sqlmodel import Session
from sqlmodel import select


def get_pano_meta(session: Session, source_image_id: str, source: PanoSource):
    statement = select(PanoMeta).where(PanoMeta.source_image_id == source_image_id and PanoMeta.source == source)
    results = session.exec(statement).first()
    return results

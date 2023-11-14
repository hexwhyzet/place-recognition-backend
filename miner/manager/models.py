from enum import Enum

from pydantic import BaseModel


class PanoType(str, Enum):
    GOOGLE_PANO = 'google_pano'


class Pano(BaseModel):
    id: str
    type: PanoType


class S3Path(BaseModel):
    bucket: str
    path: str


class IssueTask(BaseModel):
    pano: Pano
    pano_path: S3Path
    meta_path: S3Path


class FinishTask(BaseModel):
    bucket: str
    path: str


class PanoSize(BaseModel):
    width: int
    height: int


# class GooglePanoSize(PanoSize, Enum):
#     xl = PanoSize(width=13312, height=6656)
#     x = PanoSize(width=6656, height=3328)
#     m = PanoSize(width=3328, height=1664)
#     s = PanoSize(width=1664, height=832)
#     xs = PanoSize(width=416, height=208)

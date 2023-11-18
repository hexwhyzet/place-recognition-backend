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

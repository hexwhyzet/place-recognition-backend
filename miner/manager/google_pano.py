import json
from io import BytesIO
from typing import Optional

from PIL import Image
from loguru import logger

from models import S3Path
from s3 import get_object

ALLOWED_CHARS_IN_ID = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'


def check_meta(meta: S3Path) -> Optional[dict]:
    file_data = None
    try:
        content = get_object(meta.bucket, meta.path)['Body'].read()
        json_file = json.loads(content)
        for field in ['panoId', 'zoomLevel', 'lat', 'lng', 'elevation', 'rotation']:
            assert field in json_file and json_file[field] is not None
        assert 'resolution' in json_file and 'width' in json_file['resolution'] and 'height' in json_file['resolution']
        return json_file
    except Exception as e:
        logger.exception(f"google_pano uploaded meta is incorrect\n"
                         f"BUCKET: {meta.bucket}\n"
                         f"PATH: {meta.path}\n"
                         f"DATA: {file_data}")
        return None


def check_pano(pano: S3Path, meta: dict):
    try:
        response = get_object(pano.bucket, pano.path)
        file_stream = BytesIO(response['Body'].read())
        img = Image.open(file_stream)
        assert img.size == (meta['resolution']['width'], meta['resolution']['height'])
        return True
    except Exception as e:
        logger.exception(f"google_pano uploaded pano is incorrect\n"
                         f"BUCKET: {pano.bucket}\n"
                         f"PATH: {pano.path}")
        return False


def check_pano_id(pano_id: str):
    return len(pano_id) == 22 and all([letter in ALLOWED_CHARS_IN_ID for letter in pano_id])

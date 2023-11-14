import io
import os

import boto3
from PIL import Image

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
)

FILE_EXTENSION = 'JPEG'


def put_object(bucket, key, body) -> bool:
    return s3_client.put_object(Bucket=bucket, Key=key, Body=body)['ResponseMetadata']['HTTPStatusCode'] == 200


def upload_pano(bucket: str, key: str, img: Image):
    buffer = io.BytesIO()
    img.save(buffer, FILE_EXTENSION)
    buffer.seek(0)
    return put_object(bucket, key, buffer)


def upload_meta(bucket: str, key: str, json_data: str):
    return put_object(bucket, key, bytes(json_data.encode("utf-8")))

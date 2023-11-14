import io
import json
import os

import boto3
from PIL import Image

BUCKET = 'place-recognition'
DEBUG_BUCKET = 'place-recognition-debug'

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
)


def list_objects(bucket: str, prefix: str):
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    result = []
    for page in pages:
        for obj in page['Contents']:
            result.append(obj)
    return result


def get_object(bucket: str, key: str):
    return s3_client.get_object(Bucket=bucket, Key=key)


def put_object(bucket: str, key: str, body):
    return s3_client.put_object(Bucket=bucket, Key=key, Body=body)


def get_json(bucket: str, key: str) -> dict:
    return json.loads(s3_client.get_object(Bucket=bucket, Key=key)['Body'].read())


def upload_image(bucket: str, key: str, img: Image, extension: str):
    buffer = io.BytesIO()
    img.save(buffer, extension)
    buffer.seek(0)
    return put_object(bucket, key, buffer)


if __name__ == '__main__':
    # res = list_objects('place-recognition', 'google_pano')

    # print(len(res))
    print(list_objects('place-recognition', 'google_pano')[0], file=open("temp", "w"))

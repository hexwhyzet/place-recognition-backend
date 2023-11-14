import os

import boto3

s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.getenv('AWS_SERVER_PUBLIC_KEY'),
    aws_secret_access_key=os.getenv('AWS_SERVER_SECRET_KEY'),
)


def get_object(bucket: str, key: str):
    return s3_client.get_object(Bucket=bucket, Key=key)


BUCKET = 'place-recognition'

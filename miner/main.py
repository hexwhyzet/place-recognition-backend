from typing import List

from loguru import logger
import requests as requests
from celery import Celery

from db.postgres import GetSQLModelSession
from libs.coordinates import Coordinates
from libs.s3 import upload_json, upload_pyvips_image
from miner.google import GooglePanoDownloader
from models.pano import Pano, PanoSource

COUNTDOWN = 5
AUTO_RETRY_EXCEPTIONS = (Exception,)

SLEEP_SECONDS = 5
MAX_RETRIES = 5

app = Celery('miner_tasks', broker='pyamqp://guest@localhost//')

app.conf.update(
    task_serializer='pickle',
    accept_content=['pickle', 'json'],  # Optional: Accept pickle as content, but it's safer to limit it
    result_serializer='pickle',
    worker_pool='solo',
    broker_connection_retry_on_startup=True,
)

FILE_EXTENSION = 'JPEG'

requests.adapters.DEFAULT_RETRIES = 2

downloaders = {
    PanoSource.GOOGLE: GooglePanoDownloader(),
}


@app.task(name='crawl', autoretry_for=AUTO_RETRY_EXCEPTIONS,
          retry_kwargs={'countdown': COUNTDOWN, 'max_retries': MAX_RETRIES})
def crawl(coordinates: List[Coordinates], pano_source: PanoSource, threads_num: int, delay: float = 0) -> int:
    with GetSQLModelSession() as session:
        if pano_source not in downloaders:
            raise Exception(f'Source {pano_source.name} not found')

        downloader = downloaders[pano_source]
        result = downloader.crawl(session, coordinates, threads_num, delay)

        session.commit()

        return len(result)


@app.task(name='download_pano', autoretry_for=AUTO_RETRY_EXCEPTIONS,
          retry_kwargs={'countdown': COUNTDOWN, 'max_retries': MAX_RETRIES})
def download_pano(pano_id: int, bucket: str, max_zoom: int, threads_num: int) -> Pano:
    with GetSQLModelSession() as session:
        pano = session.get(Pano, pano_id)
        if pano.meta.source not in downloaders:
            raise Exception(f'Source {pano.meta.source} not found')

        downloader = downloaders[pano.meta.source]

        path_prefix = f'panos/{pano.id}'
        spec = downloader.download_spec(session, pano)
        upload_json(
            bucket=bucket,
            key=f'{path_prefix}/pano.json',
            json_data=Pano.from_orm(pano).json(),
        )
        logger.info(f'Meta uploaded to {path_prefix}/pano.json')

        for size in spec.sizes:
            if size.zoom > max_zoom:
                continue

            logger.info(f'Downloading size {size.zoom}-{size.width}x{size.height}')
            size_pyvips_image = downloader.download_pano_size(pano, size, threads_num)
            upload_pyvips_image(
                bucket=bucket,
                key=f'{path_prefix}/{size.zoom}-{size.width}x{size.height}.jpg',
                img=size_pyvips_image,
                extension=FILE_EXTENSION
            )
        session.commit()
        return pano


if __name__ == '__main__':
    # import os
    # import psutil
    # t1 = time.time()
    # download_pano(122, 'test6142623', 3, 6)
    # q = [Coordinates(55.738900170546884 - 0.004 * i, 37.61989625598907 - 0.004 * i, CoordinateSystem.ELLIPSOID) for i in range(100)]
    # res = crawl(q, PanoSource.GOOGLE, threads_num=20, delay=10)
    # print(res)
    # # print(process.memory_info().rss / 1024 ** 2, 'mb')
    # t2 = time.time()
    # print(t2 - t1, "sec")
    worker = app.Worker()
    worker.start()

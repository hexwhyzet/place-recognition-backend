import time
from typing import List

import requests
from pydantic import BaseModel

from miner.worker.yandex_pano import yandex_pano_meta_url


class YandexPanoCrawlerResult(BaseModel):
    panoId: str
    extraPanoId: str


REQUEST_DELAY = 3


def crawler_get(url: str):
    time.sleep(REQUEST_DELAY)
    return requests.get(url)


def get_crawl_url(lat: float, lng: float):
    url = f"https://api-maps.yandex.ru/services/panoramas/1.x/?l=stv&lang=ru_RU&ll={lat},{lng}&origin=userAction&provider=streetview"
    return url


def parse_pano_essentials(data):
    return data["data"]["Data"]["Images"]["imageId"], data["data"]["Data"]["panoramaId"]


def crawl_point(lat: float, lng: float):
    result: List[YandexPanoCrawlerResult] = []
    url = get_crawl_url(lat, lng)
    data = crawler_get(url).json()
    pano_id, extra_pano_id = parse_pano_essentials(data)
    result.append(YandexPanoCrawlerResult(panoId=pano_id, extraPanoId=extra_pano_id))

    for historical_pano in data["data"]["Data"]["HistoricalPanoramas"]:
        extra_pano_id = historical_pano["Connection"]["oid"]
        url = yandex_pano_meta_url(extra_pano_id)
        data = crawler_get(url).json()
        pano_id, extra_pano_id = parse_pano_essentials(data)
        result.append(YandexPanoCrawlerResult(panoId=pano_id, extraPanoId=extra_pano_id))

    for related_pano in data["data"]["Data"]["Graph"]["Node"]:
        extra_pano_id = related_pano["panoid"]

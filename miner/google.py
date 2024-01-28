import re
import datetime
import json
from typing import List

import requests
import urllib3
from geoalchemy2.shape import from_shape
from sqlmodel import Session

from db.postgres import GetSQLModelSession
from libs.coordinates import Coordinates, CoordinateSystem, MAIN_COORDINATE_SYSTEM
from libs.utils import pool_executor
from miner.common import CommonPanoDownloader
from models.pano import Pano, PanoMeta, PanoSpec, PanoSize, PanoSource
from services.common import get_or_create

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.adapters.DEFAULT_RETRIES = 3


class GooglePanoDownloader(CommonPanoDownloader):
    SOURCE = PanoSource.GOOGLE

    @staticmethod
    def crawl_url(coordinates: Coordinates) -> str:
        converted = coordinates.converted(CoordinateSystem.ELLIPSOID)
        return f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1 \
        m1!1b0!2m4!1m2!3d{converted.latitude}!4d{converted.longitude}!2d119.99999999999999!3m17!2m1!1sen!9m1!1e2!11m12 \
        !1m3!1e2!2b1!3e2!1m3!1e3!2b1!3e2!1m3!1e10!2b1!3e2!4m6!1e1!1e2!1e3!1e4!1e8!1e6&callback=_xdc_._null"

    def crawl(self, session: Session, coordinates: List[Coordinates], threads_num: int, delay: float = 0) -> List[Pano]:
        urls = [self.crawl_url(x) for x in coordinates]
        responses = pool_executor(
            items=urls,
            processor_fn=requests.get,
            max_workers=threads_num,
            executor_type="thread",
            processor_kwargs={
                'verify': False,
                'timeout': 1,
            },
            delay=delay
        )
        ans = []
        for response in responses:
            for index in set(re.findall(r"\"([a-zA-Z0-9-_]{22})\"", response.content.decode("utf-8"))):
                pano_meta, _ = get_or_create(session, PanoMeta, source_image_id=index, source=self.SOURCE)
                added_pano, _ = get_or_create(session, Pano, meta=pano_meta)
                ans.append(added_pano)
        return ans

    @staticmethod
    def spec_url(pano_meta: PanoMeta) -> str:
        return f"https://www.google.com/maps/photometa/v1?authuser=0&hl=en&gl=us&pb=!1m4!1smaps_sv.tactile!11m2!2m1!1b \
            1!2m2!1sen!2sus!3m3!1m2!1e2!2s{pano_meta.source_image_id}!4m57!1e1!1e2!1e3!1e4!1e5!1e6!1e8!1e12!2m1!1e1!4m \
            1!1i48!5m1!1e1!5m1!1e2!6m1!1e1!6m1!1e2!9m36!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e3!2b0!3e \
            3!1m3!1e8!2b0!3e3!1m3!1e1!2b0!3e3!1m3!1e4!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e3"

    def download_spec(self, session: Session, pano: Pano) -> PanoSpec:
        response = requests.get(self.spec_url(pano.meta))
        json_data = json.loads(response.content.decode("utf-8")[5:])
        geo_indo = json_data[1][0][5][0][1]
        lat = geo_indo[0][2]
        lng = geo_indo[0][3]
        bearing = geo_indo[2][0]
        north = (180 - bearing + 360) % 360

        date_base = json_data[1][0][6][7]
        timestamp = None
        if len(date_base) >= 1:
            year = date_base[0]
            month = date_base[1] if len(date_base) >= 2 else 1
            day = date_base[2] if len(date_base) >= 3 else 1
            timestamp = datetime.datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                tzinfo=datetime.timezone.utc).timestamp()

        copyright_owner = json_data[1][0][4][1][0][0][0]
        coordinates = Coordinates(latitude=lat, longitude=lng, system=CoordinateSystem.ELLIPSOID) \
            .point(MAIN_COORDINATE_SYSTEM)
        pano_spec = PanoSpec(
            coordinates=from_shape(coordinates),
            datetime=timestamp,
            direction=north,
            copyright=copyright_owner,
        )
        pano_sizes = [PanoSize(width=item[0][1], height=item[0][0], zoom=index, pano_spec=pano_spec)
                      for (index, item) in enumerate(json_data[1][0][2][3][0])]
        session.add(pano_spec)
        session.add_all(pano_sizes)
        pano.spec = pano_spec
        return pano_spec

    @staticmethod
    def zoom_to_sizes(zoom_level: int):
        return int(pow(2, zoom_level)), int(pow(2, max(0, zoom_level - 1)))

    @staticmethod
    def tile_url(pano_id: str, x: int, y: int, zoom: int):
        url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={pano_id}&zoom={zoom}&x={x}&y={y}"
        return url

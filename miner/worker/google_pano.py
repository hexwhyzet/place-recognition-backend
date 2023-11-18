import datetime
import json

import requests
from PIL import Image
from geoalchemy2.shape import from_shape

from libs.coordinates import Coordinates, CoordinateSystem, MAIN_COORDINATE_SYSTEM
from miner.worker.common_pano import pano_tile_download, pano_download
from models.pano import PanoSource, Pano, PanoMeta

requests.adapters.DEFAULT_RETRIES = 2


def zoom_to_sizes(zoom_level: int):
    return int(pow(2, zoom_level)), int(pow(2, max(0, zoom_level - 1)))


def google_pano_tile_download(pano_id: str, x: int, y: int, zoom: int):
    url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={pano_id}&zoom={zoom}&x={x}&y={y}"
    return pano_tile_download(url)


def google_pano_download(pano_meta: PanoMeta, pano: Pano, threads_num: int) -> [Pano, Image]:
    tiles_x, tiles_y = zoom_to_sizes(pano.zoom)
    return pano_download(google_pano_tile_download, pano_meta.primary_id, tiles_x, tiles_y, threads_num,
                         pano.zoom).crop((0, 0, pano.width, pano.height))


def google_meta_download(pano_id: str) -> PanoMeta:
    response = requests.get(
        f"https://www.google.com/maps/photometa/v1?authuser=0&hl=en&gl=us&pb=!1m4!1smaps_sv.tactile!11m2!2m1!1b1!2m2!1sen!2sus!3m3!1m2!1e2!2s{pano_id}!4m57!1e1!1e2!1e3!1e4!1e5!1e6!1e8!1e12!2m1!1e1!4m1!1i48!5m1!1e1!5m1!1e2!6m1!1e1!6m1!1e2!9m36!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e1!2b0!3e3!1m3!1e4!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e3")
    json_data = json.loads(response.content.decode("utf-8")[5:])
    geo_indo = json_data[1][0][5][0][1]
    lat = geo_indo[0][2]
    lng = geo_indo[0][3]
    bearing = geo_indo[2][0]
    north = (180 - bearing + 360) % 360
    year = json_data[1][0][6][7][0]
    month = json_data[1][0][6][7][1]
    coordinates = Coordinates(latitude=lat, longitude=lng, system=CoordinateSystem.ELLIPSOID).point(
        MAIN_COORDINATE_SYSTEM)
    panos = [Pano(width=item[0][1], height=item[0][0], zoom=index) for (index, item) in
             enumerate(json_data[1][0][2][3][0])]
    pano_meta = PanoMeta(
        source=PanoSource.GOOGLE,
        primary_id=pano_id,
        coordinates=from_shape(coordinates),
        datetime=datetime.datetime(year=int(year), month=int(month), day=1).timestamp(),
        direction=north,
        panos=panos,
    )
    return pano_meta


if __name__ == '__main__':
    google_meta_download('--tEeelWmZDekn9TYdvmcA', 5)

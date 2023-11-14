import json

import requests

from common_pano import pano_tile_download, pano_download

requests.adapters.DEFAULT_RETRIES = 2

SIZE_X = 32
SIZE_Y = 16


def google_pano_tile_download(pano_id: str, x: int, y: int):
    url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={pano_id}&zoom=5&x={x}&y={y}"
    return pano_tile_download(url)


def google_pano_download(pano_id: str, meta: dict, threads_num: int):
    return pano_download(google_pano_tile_download, pano_id, SIZE_X, SIZE_Y, threads_num).crop(
        (0, 0, meta['resolution']['width'], meta['resolution']['height']))


def google_meta_download(pano_id: str):
    response = requests.get(
        f"https://www.google.com/maps/photometa/v1?authuser=0&hl=ru&gl=us&pb=!1m4!1smaps_sv.tactile!11m2!2m1!1b1!2m2!1sen!2sus!3m3!1m2!1e2!2s{pano_id}!4m57!1e1!1e2!1e3!1e4!1e5!1e6!1e8!1e12!2m1!1e1!4m1!1i48!5m1!1e1!5m1!1e2!6m1!1e1!6m1!1e2!9m36!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e3!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e1!2b0!3e3!1m3!1e4!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e3")
    json_data = json.loads(response.content.decode("utf-8")[5:])
    geo_indo = json_data[1][0][5][0][1]
    lat = geo_indo[0][2]
    lng = geo_indo[0][3]
    elevation = geo_indo[1][0]
    bearing = geo_indo[2][0]
    north = (180 - bearing + 360) % 360
    year = json_data[1][0][6][7][0]
    month = json_data[1][0][6][7][1]
    height, width = json_data[1][0][2][2]
    return {
        "panoId": pano_id,
        "zoomLevel": 5,
        "lat": lat,
        "lng": lng,
        "elevation": elevation,
        "rotation": north,
        "date": {
            "year": year,
            "month": month,
        },
        "resolution": {
            "width": width,
            "height": height,
        }
    }

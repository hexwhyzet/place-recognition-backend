import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Tuple, List

import requests
from sqlmodel import Session

from libs.coordinates import Coordinates
from models import PanoMeta, Pano
from models.pano import PanoSpec, PanoSize

vipsbin = r'C:\Users\hexwh\Programming\libs\vips-dev-8.15\bin'
os.environ['PATH'] = os.pathsep.join((vipsbin, os.environ['PATH']))

import pyvips


class CommonPanoDownloader:
    @staticmethod
    def crawl_url(coordinates: Coordinates) -> str:
        raise NotImplementedError

    def crawl(self, session: Session, coordinates: List[Coordinates], threads_num: int) -> List[Pano]:
        raise NotImplementedError

    @staticmethod
    def spec_url(pano_meta: PanoMeta) -> str:
        raise NotImplementedError

    def download_spec(self, session: Session, pano: Pano) -> PanoSpec:
        raise NotImplementedError

    @staticmethod
    def zoom_to_sizes(zoom_level: int) -> Tuple[int, int]:
        raise NotImplementedError

    @staticmethod
    def tile_url(pano_id: str, x: int, y: int, zoom: int) -> str:
        raise NotImplementedError

    @staticmethod
    def download_tile(url: str) -> BytesIO:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Pano tile download is failed url: {url}.\
                Status code: {response.status_code}, {response.reason}")
        return BytesIO(response.content)

    def download_pano_size(self, pano: Pano, pano_size: PanoSize, threads_num: int) -> pyvips.Image:
        size_x, size_y = self.zoom_to_sizes(pano_size.zoom)
        if threads_num == 1:
            tiles = [[self.download_tile(self.tile_url(pano.meta.source_image_id, x, y, pano_size.zoom))
                      for x in range(size_x)] for y in range(size_y)]
        else:
            with ThreadPoolExecutor(max_workers=threads_num) as executor:
                tiles = [
                    [executor.submit(self.download_tile, self.tile_url(pano.meta.source_image_id, x, y, pano_size.zoom))
                     for x in range(size_x)] for y in range(size_y)]
                for row in tiles:
                    as_completed(row)
                tiles = [[item.result() for item in row] for row in tiles]
        pano = pyvips.Image.arrayjoin([pyvips.Image.arrayjoin([pyvips.Image.new_from_buffer(
            tile.read(), "", access="sequential") for tile in tiles_array]) for tiles_array in tiles], across=1)
        return pano.crop(0, 0, pano_size.width, pano_size.height)

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

import numpy as np
import requests
from PIL import Image
from loguru import logger

requests.adapters.DEFAULT_RETRIES = 2


def pano_tile_download(url: str) -> Image:
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Pano tile download is failed url: {url}. Status code: {response.status_code}, {response.reason}")
    else:
        logger.info(f"Response: {response.status_code}, {len(response.content)}")
    img = Image.open(BytesIO(response.content)).convert('RGB')
    return img


def pano_download(func, pano_id, size_x, size_y, threads_num=1):
    if threads_num == 1:
        tiles = [[func(pano_id, x, y) for x in range(size_x)] for y in range(size_y)]
    else:
        with ThreadPoolExecutor(max_workers=threads_num) as executor:
            tiles = [[executor.submit(func, pano_id, x, y) for x in range(size_x)] for y in range(size_y)]
            for row in tiles:
                as_completed(row)
            tiles = [[item.result() for item in row] for row in tiles]
    logger.info(f"Pano {pano_id} downloaded")
    array = np.concatenate(list(map(lambda x: np.concatenate(x, axis=1), tiles)), axis=0)
    logger.info(f"Pano {pano_id} concatenated")
    pano = Image.fromarray(array)
    logger.info(f"Pano {pano_id} converted to PIL.Image")
    return pano

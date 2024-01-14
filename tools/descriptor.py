from typing import List

import requests

from PIL import Image

from libs.coordinates import Coordinates, CoordinateSystem
from libs.features import MixVPR, SquareCrop, Resizer
from models.image import PathImage, LocalResource, ImageMeta, Direction, NdarrayImage
from network.config import get_url
from network.config import NetworkConfig


def from_local_image(path: str,
                     coordinates: Coordinates = Coordinates(0, 0, CoordinateSystem.ELLIPSOID),
                     direction: Direction = Direction(degree=0)) -> NdarrayImage:
    img = Image.open(path)
    w, h = img.size

    descriptor_extractor = MixVPR()
    square_cropper = SquareCrop()
    resizer = Resizer(descriptor_extractor.input_image_width(), descriptor_extractor.input_image_height())

    image = PathImage(
        resource=LocalResource(path=path),
        meta=ImageMeta(
            primary_id=1,
            height=h,
            width=w,
            coordinates=coordinates,
            direction=direction,
        )
    ).open()

    square_cropped = square_cropper(image)
    resized = resizer(square_cropped)
    desc_extracted = descriptor_extractor(resized)
    return list(desc_extracted)[0]


def send_recognize_request(image: NdarrayImage, network_config: NetworkConfig = None, release_name: str = None,
                           debug_token: str = None):
    data = {
        'descriptor': image.meta.descriptor.tolist(),
        'coordinates': {
            'latitude': image.meta.coordinates.latitude,
            'longitude': image.meta.coordinates.latitude,
            'system': image.meta.coordinates.system.value,
        },
        'direction': image.meta.direction.degree,
    }

    if release_name is not None:
        data['release_name'] = release_name

    if debug_token is not None:
        data['debug_token'] = debug_token

    url = get_url('recognize', network_config)
    return requests.post(url=url, json=data)

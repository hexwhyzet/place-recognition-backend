import datetime
import glob
import json
import os
from enum import Enum
from typing import List

import numpy as np

from libs.coordinates import CoordinateSystem, Coordinates
from libs.s3 import BUCKET, list_objects, get_json
from libs.utils import rle2mask
from models.image import PathImage, Direction, ImageMeta, Layer, ImageSource, S3Resource, ImageType


class PanoDir(Enum):
    google_pano = "google_pano"


pano_source_to_dir = {
    ImageSource.GOOGLE: PanoDir.google_pano
}

pano_source_to_coordinate_system = {
    ImageSource.GOOGLE: CoordinateSystem.ELLIPSOID
}


def pano_ids(bucket: str = BUCKET, sources=None):
    if sources is None:
        sources = pano_source_to_dir.values()
    elif isinstance(sources, ImageSource):
        sources = [pano_source_to_dir[sources].value]
    elif isinstance(sources, PanoDir):
        sources = [sources.value]
    elif isinstance(sources, str):
        sources = [sources]
    elif isinstance(sources, List):
        if not all(map(lambda x: isinstance(x, ImageSource), sources)):
            raise Exception("Incorrect type in sources, should be ImageSource or List[ImageSource]")
    result = []
    for prefix in sources:
        objects = list_objects(bucket, prefix)
        ids = list(
            filter(lambda x: x != '', set(obj["Key"].removeprefix(f"{prefix}/").split("/")[0] for obj in objects)))
        result.extend(ids)
    return result


def parse_meta(meta: dict, source: ImageSource, zoom: int) -> ImageMeta:
    size = [pano_size for pano_size in meta['panos'] if pano_size['zoom'] == zoom][0]
    return ImageMeta(
        primary_id=meta['primary_id'],
        type=ImageType.PANO,
        source=source,
        height=size['height'],
        width=size['width'],
        direction=Direction(degree=meta['direction']),
        coordinates=Coordinates(
            latitude=meta['coordinates']['latitude'],
            longitude=meta['coordinates']['longitude'],
            system=pano_source_to_coordinate_system[source],
        ),
        datetime=datetime.datetime.fromisoformat(meta['datetime']),
    )


def google_street_view_local(subpath: str = "") -> List[PathImage]:
    base_path = os.path.join('/Users/kabakov/PycharmProjects/place-recognition/Research/Server/images/google', subpath)
    images = []
    for raw_meta_path in glob.glob(os.path.join(base_path, "*.json")):
        raw_meta = json.loads(open(raw_meta_path, 'r').read())
        image = PathImage(
            path=os.path.join(base_path, raw_meta['filename']),
            meta=parse_meta(raw_meta, ImageSource.GOOGLE)
        )
        images.append(image)
    return images


def path_pano_from_s3(pano_id: str, source: ImageSource, zoom: int, bucket: str = BUCKET,
                      preload_content: bool = False) -> PathImage:
    base = os.path.join(pano_source_to_dir[source].value, pano_id)
    meta_path = os.path.join(base, "meta.json")
    meta_raw = get_json(bucket, meta_path)
    meta = parse_meta(meta_raw, source, zoom)
    pano_path = os.path.join(base, f"{meta.width}x{meta.height}.jpg")
    s3_resource = S3Resource(path=pano_path, bucket=BUCKET)
    if preload_content:
        s3_resource.load_content()
    return PathImage(
        resource=s3_resource,
        meta=parse_meta(meta_raw, source, zoom)
    )


def read_coco_dataset(path):
    annotations_path = os.path.join(path, "annotations/instances_default.json")
    coco_annotations = json.loads(open(annotations_path, "r").read())
    images_path = os.path.join(path, "images")
    images = coco_annotations["images"]
    categories = coco_annotations["categories"]
    annotations = coco_annotations["annotations"]
    real_id_by_category_id = {category["id"]: int(category["name"][2:]) for category in categories}

    result = []

    for image in images:
        width = image["width"]
        height = image["height"]
        res_annotation = np.zeros((height, width), dtype=np.int32)
        for annotation in annotations:
            if annotation["image_id"] != image["id"]:
                continue

            assert height == annotation["segmentation"]["size"][0]
            assert width == annotation["segmentation"]["size"][1]
            rle = annotation["segmentation"]["counts"]
            mask = rle2mask(rle, (width, height))
            res_annotation[mask] = real_id_by_category_id[annotation["category_id"]]
        path_image = PathImage(
            path=os.path.join(images_path, image["file_name"]),
            meta=ImageMeta(
                type='flat',
                height=height,
                width=width,
                annotations=Layer(content=res_annotation),
            )
        )
        result.append(path_image.open())
    return result


if __name__ == '__main__':
    print(path_pano_from_s3(ImageSource.GOOGLE, "CbJJWBPgHlwlufOmygJFwg"))
    # dataset = read_coco_dataset(
    #     "/Users/kabakov/PycharmProjects/place-recognition/Research/Server/images/place-recognition-sur-coco")
    # test_image = dataset[70]
    # test_image.save("TestImage.jpg")
    # test_image.meta.annotations.debug_save("TestAnnot.jpg")
    # print(test_image.image.content.shape)
    # print(test_image.meta.annotations.content.shape)

import itertools
import time
from copy import deepcopy
from typing import List, Union, Iterator

import numpy as np
import torch
from sqlmodel import Session

import ml_models.mixvpr.interface as mixvpr_interface
from libs.coordinates import CoordinateSystem
from libs.equirec_to_perspec import Equirectangular
from libs.geo import decompose_angles
from models import Building
from models.image import NdarrayImage, Layer, ImageType
from services.geo import select_closest_geo_objects_to_point


class FeatureGenerator:
    name: str = 'default'

    def __call__(self, images: Union[NdarrayImage, Iterator[NdarrayImage]]) -> Iterator[NdarrayImage]:
        if isinstance(images, NdarrayImage):
            images = [images]
        for image in self.transform(images):
            image.meta.transformations.append(self.name)
            yield image

    def transform(self, image: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        raise Exception("Transform is not implemented")


class Cropper(FeatureGenerator):
    name = 'cropper'

    def __init__(self, width, height, width_stride=None, height_stride=None):
        self.height = height
        self.width = width
        self.height_stride = height_stride or height
        self.width_stride = width_stride or width

    def transform(self, images: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        for image in images:
            for height_end in range(self.height, image.height + 1, self.height_stride):
                for width_end in range(self.width, image.width + 1, self.width_stride):
                    width_start = width_end - self.width
                    height_start = height_end - self.height
                    yield image.crop(width_start=width_start,
                                     width_end=width_end,
                                     height_start=height_start,
                                     height_end=height_end)


class Resizer(FeatureGenerator):
    name = 'scaler'

    def __init__(self, width=None, height=None, width_scale=None, height_scale=None):
        self.width = width
        self.height = height
        self.width_scale = width_scale
        self.height_scale = height_scale

    def transform(self, images: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        for image in images:
            res = image.resize(width=self.width,
                               height=self.height,
                               width_scale=self.width_scale,
                               height_scale=self.height_scale)
            yield res


class SquareCrop(FeatureGenerator):
    name = 'square_crop'

    def transform(self, images: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        for image in images:
            yield image.square_crop()


class DescriptorExtractor(FeatureGenerator):
    name = 'descriptor'

    def __init__(self, batch_size: int = 1):
        self.batch_size = batch_size

    def transform(self, images: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        while batch_images := list(itertools.islice(images, self.batch_size)):
            descriptors = self.descriptor(iter(batch_images))
            for image, descriptor in zip(batch_images, descriptors):
                image.meta.descriptor = descriptor
                image.meta.descriptor_image = deepcopy(image.image)
                yield image

    def descriptor(self, images: Iterator[NdarrayImage]) -> np.array:
        raise NotImplementedError

    def descriptor_size(self):
        raise NotImplementedError

    def input_image_height(self):
        raise NotImplementedError

    def input_image_width(self):
        raise NotImplementedError


class MixVPR(DescriptorExtractor):
    DESCRIPTOR_SIZE = 4096
    INPUT_IMAGE_HEIGHT = 320
    INPUT_IMAGE_WIDTH = 320

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = mixvpr_interface.get_loaded_model()

    def descriptor(self, images: Iterator[NdarrayImage]) -> np.ndarray:
        # for image in images:
        #     assert image.image.content.shape == (320, 320, 3)
        # a = time.time()
        # print("Started")
        batch = torch.tensor(
            np.fromiter((np.moveaxis(image.image.content, [2], [0]) for image in images),
                        dtype=(np.float32, (3, 320, 320))))
        # b = time.time()
        # print(f"Assembled: {b - a}")
        # print(f"Images: {len(batch)}")
        res = self.model(batch).detach().numpy()
        # c = time.time()
        # print(f"Model: {c - b}")
        return res

    def descriptor_size(self):
        return self.DESCRIPTOR_SIZE

    def input_image_height(self):
        return self.INPUT_IMAGE_HEIGHT

    def input_image_width(self):
        return self.INPUT_IMAGE_WIDTH


class PanoGeoCropper(FeatureGenerator):
    name = 'pano_cropper'
    filter_buildings_indices = []

    def __init__(self, session: Session, angle_threshold: int = 30, padding: int = 0,
                 buildings: Union[int, List[int]] = None):
        self.session = session
        if isinstance(buildings, List):
            assert all(map(lambda x: isinstance(x, int), buildings))
            self.filter_buildings_indices = buildings
        elif isinstance(buildings, int):
            self.filter_buildings_indices = [buildings]
        elif buildings is None:
            self.filter_buildings_indices = []
        else:
            raise Exception(f"Incorrect filter_buildings_indices type")
        self.padding = padding
        self.angle_threshold = angle_threshold

    def transform(self, images: Iterator[NdarrayImage]) -> Iterator[NdarrayImage]:
        for image in images:
            observer_point = image.meta.coordinates.point(CoordinateSystem.PROJECTION)
            closest_buildings = select_closest_geo_objects_to_point(self.session, Building, observer_point, 15)
            angles = decompose_angles(closest_buildings, observer_point)
            equ = Equirectangular(image.image.content)
            for start, end, index, avg_distance in angles:
                if not index:
                    continue

                if self.filter_buildings_indices and index not in self.filter_buildings_indices:
                    continue

                if start > end or end - start < self.angle_threshold:
                    # TODO process split angle case
                    continue

                end += self.padding
                start -= self.padding
                fov = end - start
                shift = 360 - image.meta.direction.degree
                pixels_per_fov_degree = (image.width / 360) / 2
                # height_k = 45 / avg_distance
                # height = min(4000, 2000 * height_k)
                img = equ.GetPerspective(fov, -shift + start - 180 + fov / 2, 10, 2000, pixels_per_fov_degree * fov)
                ndarray_image = NdarrayImage(
                    image=Layer(content=img),
                    meta=image.meta.copy(
                        update={
                            'type': ImageType.FLAT,
                            'recognised_building_id': index
                        },
                        deep=True
                    )
                )
                yield ndarray_image


class FeaturePipeline(FeatureGenerator):
    def __init__(self, feature_generators: Iterator[FeatureGenerator]):
        self.feature_generators = feature_generators

    def __call__(self, images: Union[NdarrayImage, Iterator[NdarrayImage]]):
        for feature_generator in self.feature_generators:
            for intermediate_result in feature_generator(images):
                yield intermediate_result

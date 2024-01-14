import datetime as dt
import time
from copy import deepcopy
from enum import Enum
from io import BytesIO
from typing import Optional, Callable

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

import libs.s3 as s3
from libs.coordinates import Coordinates

Image.MAX_IMAGE_PIXELS = 933120000
FILE_EXTENSION = 'jpeg'


class ImageType(str, Enum):
    FLAT = 'flat'
    PANO = 'pano'


class ImageSource(str, Enum):
    OWN = 'own'
    GOOGLE = 'google'


class BaseResource(BaseModel):
    path: str


class LocalResource(BaseResource):
    pass


class S3Resource(BaseResource):
    bucket: str
    content: Optional[dict] = None

    @property
    def url(self):
        return f'https://storage.yandexcloud.net/{self.bucket}/{self.path}'

    def load_content(self):
        self.content = s3.get_object(self.bucket, self.path)

    def get_content(self):
        if self.content is None:
            self.load_content()
        return self.content


class Direction(BaseModel):
    degree: float


class Layer(BaseModel):
    content: np.ndarray

    class Config:
        arbitrary_types_allowed = True

    @property
    def width(self):
        return self.content.shape[1]

    @property
    def height(self):
        return self.content.shape[0]

    def resize(self, width, height):
        return Layer(
            content=cv2.resize(
                self.content,
                dsize=(width, height),
                interpolation=cv2.INTER_NEAREST,
            ),
        )

    def crop(self, width_start, width_end, height_start, height_end):
        return Layer(
            content=self.content[height_start:height_end, width_start:width_end],
        )

    def center_crop(self, width, height):
        dim_width, dim_height = width, height
        crop_width = dim_width if dim_width < self.width else self.width
        crop_height = dim_height if dim_height < self.height else self.height
        mid_x, mid_y = int(self.width / 2), int(self.height / 2)
        cw2, ch2 = int(crop_width / 2), int(crop_height / 2)
        return self.crop(mid_x - cw2, mid_x + cw2, mid_y - ch2, mid_y + ch2)

    def square_crop(self):
        square_side = min(self.width, self.height)
        return self.center_crop(square_side, square_side)

    def debug_save(self, path):
        plt.imsave(path, self.content, cmap='gray')
        # cv2.imwrite(path, self.content)

    @property
    def pil_image(self):
        return Image.fromarray(self.content)

    def debug(self, base_resource: BaseResource, extension: str):
        if isinstance(base_resource, LocalResource):
            cv2.imwrite(base_resource.path, cv2.cvtColor(self.content, cv2.COLOR_RGB2BGR))
        elif isinstance(base_resource, S3Resource):
            s3.upload_image(base_resource.bucket, base_resource.path, self.pil_image, extension)
        else:
            raise Exception("Unknown BaseResource subtype")


class ImageMeta(BaseModel):
    primary_id: str
    height: int
    width: int
    type: ImageType = ImageType.FLAT
    source: ImageSource = ImageSource.OWN
    coordinates: Coordinates
    direction: Direction
    datetime: Optional[dt.datetime] = None
    transformations: list = Field(default_factory=list)
    tags: list = Field(default_factory=list)
    annotations: Layer = None
    descriptor: Optional[np.ndarray]
    recognised_building_id: Optional[int]
    descriptor_image: Layer = None

    class Config:
        arbitrary_types_allowed = True


class PathImage(BaseModel):
    resource: BaseResource
    meta: ImageMeta

    def open(self):
        if isinstance(self.resource, S3Resource):
            file_stream = BytesIO(self.resource.get_content()['Body'].read())
            img = Image.open(file_stream)
        elif isinstance(self.resource, LocalResource):
            img = Image.open(self.resource.path)
        else:
            raise Exception("unknown ResourceType value")
        return NdarrayImage(image=Layer(content=np.array(img.convert("RGB"))), meta=deepcopy(self.meta))

    def save(self, base_resource: BaseResource):
        pass


class NdarrayImage(BaseModel):
    image: Layer
    meta: ImageMeta

    @property
    def width(self):
        return self.image.width

    @property
    def height(self):
        return self.image.height

    def check_layer_dimensions(self):
        for layer in [self.meta.annotations]:
            if layer is not None:
                assert layer.height == self.height and layer.width == self.width

    def __post_init__(self):
        self.check_layer_dimensions()

    def __modify_layers(self, f: Callable[[Layer], Layer]):
        new_meta = deepcopy(self.meta)
        if new_meta.annotations:
            new_meta.annotations = f(self.meta.annotations)
        return NdarrayImage(
            image=f(self.image),
            meta=new_meta,
        )

    def resize(self, width=None, height=None, width_scale=None, height_scale=None):
        if width is None:
            if width_scale is None:
                raise Exception("width or width_scale should be specified")
            width = int(self.meta.width * width_scale)
        if height is None:
            if height_scale is None:
                raise Exception("height or height_scale should be specified")
            height = int(self.meta.height * height_scale)
        return self.__modify_layers(lambda layer: layer.resize(width, height))

    def crop(self, width_start, width_end, height_start, height_end):
        return self.__modify_layers(lambda layer: layer.crop(width_start, width_end, height_start, height_end))

    def center_crop(self, width, height):
        return self.__modify_layers(lambda layer: layer.center_crop(width, height))

    def square_crop(self):
        return self.__modify_layers(lambda layer: layer.square_crop())

    # def save(self, base_resource: BaseResource) -> PathImage:
    #     if isinstance(base_resource, LocalResource):
    #         cv2.imwrite(base_resource.path, cv2.cvtColor(self.image.content, cv2.COLOR_RGB2BGR))
    #         return PathImage(resource=base_resource, meta=deepcopy(self.meta))
    #     elif isinstance(base_resource, S3Resource):
    #         buffer = io.BytesIO()
    #         Image.fromarray(self.image.content).save(buffer, FILE_EXTENSION)
    #         buffer.seek(0)
    #         s3.put_object(base_resource.bucket, base_resource.path, buffer)
    #         return PathImage(resource=base_resource, meta=deepcopy(self.meta))
    #     else:
    #         raise Exception("Unknown BaseResource subtype")
    #
    # def debug(self, base_resource: BaseResource) -> PathImage:
    #     if isinstance(base_resource, LocalResource):
    #         cv2.imwrite(base_resource.path, cv2.cvtColor(self.image.content, cv2.COLOR_RGB2BGR))
    #         return PathImage(resource=base_resource, meta=deepcopy(self.meta))
    #     elif isinstance(base_resource, S3Resource):
    #         buffer = io.BytesIO()
    #         Image.fromarray(self.image.content).save(buffer, FILE_EXTENSION)
    #         buffer.seek(0)
    #         s3.put_object(base_resource.bucket, base_resource.path, buffer)
    #         return PathImage(resource=base_resource, meta=deepcopy(self.meta))
    #     else:
    #         raise Exception("Unknown BaseResource subtype")

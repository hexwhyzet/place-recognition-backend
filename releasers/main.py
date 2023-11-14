import dataclasses
from copy import deepcopy

import ray
from loguru import logger
from sqlmodel import Session
from tqdm import tqdm

from db.postgres import GetSQLModelSession
from db.qdrant import GetQdrantClient
from libs.features import Resizer, PanoGeoCropper, DescriptorExtractor, MixVPR, SquareCrop
from libs.filter import AreaPathImageFilter
from libs.readers import path_pano_from_s3, pano_ids
from libs.s3 import DEBUG_BUCKET
from libs.utils import generate_release_name, generate_hex_uuid, pool_executor
from models import Release
from models.geo import Area
from models.image import PathImage, ImageSource, S3Resource, FILE_EXTENSION
from resources.areas.main import PODKOPAEVSKY_PEREULOK
from services.release import create_release, create_vector_release, create_release_item, \
    export_release


@dataclasses.dataclass
class RemoteConfig:
    active: bool = False
    num_workers: int = 1


class Config:
    arbitrary_types_allowed = True


@dataclasses.dataclass
class ReleaseConfig:
    area: Area
    source: ImageSource
    descriptor_extractor: DescriptorExtractor
    remote: RemoteConfig
    name: str = dataclasses.field(default_factory=generate_release_name)

    class Config:
        arbitrary_types_allowed = True


class Releaser:
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.descriptor_extractor = self.config.descriptor_extractor
        with GetSQLModelSession() as session:
            db_release = create_release(session=session, name=self.config.name)
            qdrant_client = GetQdrantClient()
            create_vector_release(
                client=qdrant_client,
                collection_name=db_release.name,
                vector_size=self.config.descriptor_extractor.descriptor_size()
            )
            self.release_name = db_release.name

            pano_ids_from_source = pano_ids(sources=self.config.source)

            path_images = pool_executor(
                items=pano_ids_from_source,
                processor_fn=path_pano_from_s3,
                processor_args=[self.config.source],
                tqdm_desc="Downloading panos",
                max_workers=40,
            )

            area_filter = AreaPathImageFilter(self.config.area)
            filtered_path_images = []
            for path_image in tqdm(path_images, desc="Filtering panos"):
                if area_filter.filter(path_image):
                    filtered_path_images.append(path_image)

            if not self.config.remote.active:
                item_releaser = RealeaseItemGenerator(self.config, db_release, session)
                release_items_lists = pool_executor(
                    items=filtered_path_images,
                    processor_fn=item_releaser.release_item,
                    processor_args=[],
                    tqdm_desc="Releasing panos",
                    max_workers=5,
                )

                for release_items in release_items_lists:
                    session.add_all(release_items)
                session.commit()

            else:
                raise Exception("Distributed generation is not implemented yet")
            #     ray.init()
            #     actors = [RemoteRealeaseItemGenerator.remote(self.config) for _ in range(5)]
            #     pool = ActorPool(actors)
            #     results = list(
            #         pool.map_unordered(
            #             fn=lambda actor, value: actor.release.remote(value),
            #             values=path_images_in_selected_area
            #         )
            #     )
            export_release(qdrant_client, db_release)
            logger.info(f"Release {self.release_name} is ready!")


class RealeaseItemGenerator:
    def __init__(self, config: ReleaseConfig, release: Release, session: Session):
        self.config = config
        self.sesion = session
        self.vector_db_client = GetQdrantClient()
        self.geo_cropper = PanoGeoCropper(self.sesion)
        self.descriptor_extractor = config.descriptor_extractor
        self.square_cropper = SquareCrop()
        self.resizer = Resizer(self.descriptor_extractor.input_image_width(),
                               self.descriptor_extractor.input_image_height())
        self.release: Release = release

    def release_item(self, path_image: PathImage):
        result = []
        for processed_image in self.descriptor_extractor(
                self.resizer(
                    self.square_cropper(
                        self.geo_cropper(
                            path_image.open())))):
            if any(x is None for x in [processed_image.meta.descriptor,
                                       processed_image.meta.coordinates,
                                       processed_image.meta.recognised_building_id]):
                logger.info("Empty descriptor or coordinates or recognised_building_id got")
                continue

            debug_image = S3Resource(
                path=f'releases/{self.config.name}/{generate_hex_uuid()}.{FILE_EXTENSION}',
                bucket=DEBUG_BUCKET,
            )

            processed_image.image.debug(debug_image, FILE_EXTENSION)

            release_item = create_release_item(
                release=self.release,
                descriptor=processed_image.meta.descriptor.tolist(),
                coordinates=processed_image.meta.coordinates,
                building_id=processed_image.meta.recognised_building_id,
                image_url=debug_image.url,
            )
            result.append(release_item)
        return result


@ray.remote
class RemoteRealeaseItemGenerator(RealeaseItemGenerator):
    pass


if __name__ == '__main__':
    my_config = ReleaseConfig(
        area=deepcopy(PODKOPAEVSKY_PEREULOK),
        source=ImageSource.GOOGLE,
        descriptor_extractor=MixVPR(),
        remote=RemoteConfig(
            active=False,
            num_workers=1,
        ),
    )
    Releaser(my_config)

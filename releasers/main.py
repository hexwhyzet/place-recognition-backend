import dataclasses
from copy import deepcopy
from dataclasses import dataclass
from typing import Iterator

from loguru import logger
from tqdm import tqdm

from db.postgres import GetSQLModelSession
from db.qdrant import GetQdrantClient
from libs.features import Resizer, PanoGeoCropper, DescriptorExtractor, MixVPR, SquareCrop
from libs.filter import AreaPathImageFilter
from libs.readers import path_pano_from_s3, pano_ids
from libs.s3 import DEBUG_BUCKET
from libs.utils import generate_release_name, generate_hex_uuid, pool_executor, chunks
from models import Release
from models.geo import Area
from models.image import PathImage, ImageSource, S3Resource, FILE_EXTENSION
from resources.areas.main import ZAMOSKVORECHE
from services.release import create_release, create_vector_release, create_release_item, \
    export_release_items


@dataclass
class RemoteConfig:
    active: bool = False
    num_workers: int = 1


class Config:
    arbitrary_types_allowed = True


@dataclass
class DescriptorConfig:
    extractor: type(DescriptorExtractor)
    batch_size: int = 1
    device: str = 'cpu'


@dataclasses.dataclass
class ReleaseConfig:
    area: Area
    source: ImageSource
    descriptor_config: DescriptorConfig
    remote: RemoteConfig
    zoom: int
    name: str = dataclasses.field(default_factory=generate_release_name)

    class Config:
        arbitrary_types_allowed = True


class Releaser:
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.descriptor_extractor = self.config.descriptor_config.extractor(
            batch_size=self.config.descriptor_config.batch_size
        )
        with GetSQLModelSession() as session:
            db_release = create_release(session=session, name=self.config.name)
            qdrant_client = GetQdrantClient()
            create_vector_release(
                client=qdrant_client,
                collection_name=db_release.name,
                vector_size=self.descriptor_extractor.descriptor_size()
            )
            self.release_name = db_release.name

            pano_ids_from_source = pano_ids(sources=self.config.source)

            for chunk in tqdm(list(chunks(pano_ids_from_source, 1024)), desc="Parsing chunks"):
                # for chunk in tqdm(chunks(pano_ids_from_source, 1024), desc="Parsing chunks"):
                path_images = pool_executor(
                    items=chunk,
                    processor_fn=path_pano_from_s3,
                    processor_args=[self.config.source, self.config.zoom],
                    processor_kwargs={"preload_content": False},
                    tqdm_desc="Downloading panos",
                    max_workers=10,
                )

                area_filter = AreaPathImageFilter(self.config.area)
                filtered_path_images = []
                for path_image in tqdm(path_images, desc="Filtering panos"):
                    if area_filter.filter(path_image):
                        filtered_path_images.append(path_image)

                if not self.config.remote.active:
                    chunked_filtered_path_images = chunks(filtered_path_images, 64)
                    _ = pool_executor(
                        items=list(chunked_filtered_path_images),
                        processor_fn=generate_release_items,
                        processor_args=[config, db_release.id],
                        processor_kwargs=dict(),
                        tqdm_desc="Releasing panos",
                        max_workers=8,
                    )
                else:
                    raise Exception("Distributed generation is not implemented yet")
                    # ray.init()
                    # actors = [RemoteRealeaseItemGenerator.remote(self.config) for _ in range(5)]
                    # pool = ActorPool(actors)
                    # results = list(
                    #     pool.map_unordered(
                    #         fn=lambda actor, value: actor.release.remote(value),
                    #         values=path_images_in_selected_area
                    #     )
                    # )
            # end_timetamp = time.time()
            # logger.info(f"Exporting release {self.release_name} has started...")
            # export_release(qdrant_client, db_release)
            # logger.info(f"Release {self.release_name} is ready!\nWithin {start_timetamp - end_timetamp} seconds")


def generate_release_items(path_images: Iterator[PathImage], config: ReleaseConfig, db_release_id):
    with GetSQLModelSession() as session:
        geo_cropper = PanoGeoCropper(session)
        descriptor_extractor = config.descriptor_config.extractor(
            batch_size=config.descriptor_config.batch_size
        )
        square_cropper = SquareCrop()
        resizer = Resizer(descriptor_extractor.input_image_width(), descriptor_extractor.input_image_height())
        release = session.get(Release, db_release_id)

        release_items = []
        for processed_image in \
                descriptor_extractor(
                    resizer(
                        square_cropper(
                            geo_cropper(
                                (path_image.open() for path_image in path_images))))):
            if any(x is None for x in [processed_image.meta.descriptor,
                                       processed_image.meta.coordinates,
                                       processed_image.meta.recognised_building_id]):
                logger.info("Empty descriptor or coordinates or recognised_building_id got")
                continue

            debug_image = S3Resource(
                path=f'releases/{config.name}/{generate_hex_uuid()}.{FILE_EXTENSION}',
                bucket=DEBUG_BUCKET,
            )

            processed_image.image.debug(debug_image, FILE_EXTENSION)

            release_item = create_release_item(
                release=release,
                descriptor=processed_image.meta.descriptor.tolist(),
                coordinates=processed_image.meta.coordinates,
                building_id=processed_image.meta.recognised_building_id,
                image_url=debug_image.url,
            )
            release_items.append(release_item)

        session.add_all(release_items)
        session.commit()

        qdrant_client = GetQdrantClient()

        export_release_items(qdrant_client, release, release_items)

        print("BATCH EXPORTED")


if __name__ == '__main__':
    my_config = ReleaseConfig(
        # area=deepcopy(DEMO_ZAMOSKVORECHE_STREET),
        area=deepcopy(ZAMOSKVORECHE),
        source=ImageSource.GOOGLE,
        descriptor_config=DescriptorConfig(
            extractor=MixVPR,
            batch_size=8,
            device='cuda:0'
        ),
        remote=RemoteConfig(
            active=False,
            num_workers=1,
        ),
        zoom=3,
    )
    Releaser(my_config)

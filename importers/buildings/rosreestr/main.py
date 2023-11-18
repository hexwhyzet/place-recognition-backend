import geopandas as gp
import pandas as pd
from loguru import logger
from tqdm import tqdm

from db.postgres import GetSQLModelSession
from models import BuildingGroup, Building
from resources.areas.main import MOSCOW_GARDEN_RING
from services.language import create_text_content

MOSCOW_PATH = "resources/buildings/rosreestr/moscow.gpkg"


def update_buildings_table():
    logger.info(f"{MOSCOW_PATH} is loading...")
    df = gp.read_file(MOSCOW_PATH)
    logger.info(f"{MOSCOW_PATH} is loaded")
    with GetSQLModelSession() as session:

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            geometry = row.at['geometry']
            name = row.at['r_name']
            address = row.at['r_adress']
            # style = row.at['r_style']
            # architect = row.at['r_architect']
            image_url = row.at['r_photo_url']
            year = row.at['r_year_int']

            if not MOSCOW_GARDEN_RING.contains(geometry):
                continue

            building_group = BuildingGroup()

            if name is not None:
                name_text_content = create_text_content(session=session, RU=name)
                building_group.title_id = name_text_content.id

            if not pd.isna(year):
                building_group.construction_year = int(year)

            prefix = "http://"
            if image_url is not None and image_url[:len(prefix)] == prefix:
                building_group.image_url = image_url

            session.add(building_group)
            session.flush()

            building = Building(
                group_id=building_group.id
            )

            if address is not None:
                address_text_content = create_text_content(session=session, RU=address)
                building.address_id = address_text_content.id

            building.set_geometry_shape(geometry)

            session.add(building)

        session.commit()


if __name__ == '__main__':
    update_buildings_table()

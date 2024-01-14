import json
import os

from sqlmodel import select

from db.postgres import GetSQLModelSession
from models.geo import MetroLine, MetroStation
from services.language import create_text_content

METRO_DATA_PATH = "resources/metro/data.json"


def update_metro_tables():
    if not os.path.exists(METRO_DATA_PATH):
        raise "Metro data JSON file does not exists"

    with open("resources/metro/data.json", "r", encoding="utf8") as input_file:
        data = json.loads(input_file.read())

    with GetSQLModelSession() as session:

        for line in data:
            line_name = line['name']
            statement = select(MetroLine).where(MetroLine.id == line['id'])
            metro_line = session.exec(statement).first()
            if metro_line is None:
                line_text_content = create_text_content(session=session, RU=line_name)
                metro_line = MetroLine(
                    id=line['id'],
                    name_id=line_text_content.id
                )
                session.add(metro_line)
                session.flush()

            for station in line['stations']:
                statement = select(MetroStation).where(MetroStation.id == station['id'])
                metro_station = session.exec(statement).first()
                if metro_station is None:
                    station_text_content = create_text_content(session=session, RU=station['name'])
                    metro_station = MetroStation(
                        id=station['id'],
                        name_id=station_text_content.id,
                        line_id=metro_line.id,
                        coordinates=f"POINT({station['lat']} {station['lng']})"
                    )
                    session.add(metro_station)

        session.commit()


if __name__ == '__main__':
    update_metro_tables()

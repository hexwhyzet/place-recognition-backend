from geoalchemy2.shape import to_shape
from sqlmodel import select

from db.postgres import GetSQLModelSession
from models.geo import Building
from models.link import BuildingMetroLink
from services.geo import select_closest_metro_stations
from sqlmodel import delete


def update_building_to_metro():
    with GetSQLModelSession() as session:
        for building in session.exec(select(Building)).all():
            session.exec(delete(BuildingMetroLink).where(BuildingMetroLink.building_id == building.id))
            closest_stations = []
            for index, metro_station in enumerate(select_closest_metro_stations(session, building, 3)):
                if index == 0 or building.distance(to_shape(metro_station.coordinates)) < 1000:
                    closest_stations.append(metro_station)
            for index, closest_station in enumerate(closest_stations):
                link = BuildingMetroLink(
                    building_id=building.id,
                    metro_station_id=closest_station.id,
                    priority=index,
                )
                session.add(link)
        session.commit()


if __name__ == '__main__':
    update_building_to_metro()

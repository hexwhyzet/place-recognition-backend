import json
import os.path

import requests

from libs.coordinates import Coordinates, CoordinateSystem

STARTING_INDEX = 1


class ParsedMetroStations:
    def __init__(self, path):
        self.path = path
        self.parsed_data = []
        if os.path.exists(path):
            try:
                with open(self.path, "r") as input_file:
                    self.parsed_data = json.loads(input_file.read())
            except Exception as e:
                Warning("Error occured on metro parsing")

    def save(self):
        data = json.dumps(self.parsed_data, ensure_ascii=False)
        with open(self.path, "w") as output:
            output.write(data)

    def has_station(self, line_name, station_name):
        for line in self.parsed_data:
            for station in line['stations']:
                if line['name'] == line_name and station['name'] == station_name:
                    return True
        return False

    def has_line(self, line_name):
        for line in self.parsed_data:
            if line['name'] == line_name:
                return True

    def next_line_id(self):
        result_id = STARTING_INDEX - 1
        for line in self.parsed_data:
            result_id = max(result_id, line['id'])
        return result_id + 1

    def next_station_id(self):
        result_id = STARTING_INDEX - 1
        for line in self.parsed_data:
            for station in line['stations']:
                result_id = max(result_id, station['id'])
        return result_id + 1

    def add_station(self, line_name, station_name, lat, lng):
        if not self.has_line(line_name):
            self.parsed_data.append({
                'id': self.next_line_id(),
                'name': line_name,
                'stations': [{
                    'id': self.next_station_id(),
                    'name': station_name,
                    'lat': lat,
                    'lng': lng
                }]
            })
            return

        if not self.has_station(line_name, station_name):
            for i in range(len(self.parsed_data)):
                if self.parsed_data[i]['name'] == line_name:
                    self.parsed_data[i]['stations'].append({
                        'id': self.next_station_id(),
                        'name': station_name,
                        'lat': lat,
                        'lng': lng
                    })
            return
        return


def flatten(input):
    new_list = []
    for i in input:
        for j in i:
            new_list.append(j)
    return new_list


def is_station_parsed(parsed_data, station_name, line_name):
    for parsed_line in parsed_data:
        if parsed_line['name'] != line_name:
            continue

        for parsed_station in parsed_line['stations']:
            if parsed_station['name'] == station_name:
                return True
    return False


external_resources = "https://api.hh.ru/metro/1"
data_json = requests.get(external_resources).json()

parsed_data = ParsedMetroStations('./data.json')

flatten_stations = flatten(list(map(lambda x: x['stations'], data_json['lines'])))

for flatten_station in flatten_stations:
    station_name = flatten_station['name']
    line_name = flatten_station['line']['name']
    lat = flatten_station['lat']
    lng = flatten_station['lng']
    coords = Coordinates(
        latitude=lat,
        longitude=lng,
        system=CoordinateSystem.ELLIPSOID,
    ).converted(CoordinateSystem.ELLIPSOID)
    parsed_data.add_station(
        line_name=line_name,
        station_name=station_name,
        lat=coords.latitude,
        lng=coords.longitude
    )

parsed_data.save()

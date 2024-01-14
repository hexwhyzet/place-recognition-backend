import math
from statistics import mean

import numpy as np
from shapely import LineString, distance
from shapely.geometry import Point
from shapely.ops import nearest_points

from libs.utils import rle_encode
from models import Building


def decompose_angles(buildings: Building, observer_point: Point, iterations: int = 360 * 4, ray_length: float = 10000):
    angle_map = []
    for i in np.linspace((1 / 2) * math.pi, -(3 / 2) * math.pi, iterations) + 2 * math.pi / iterations / 2:
        observer_point_coords = observer_point.coords[0]
        shifted_point_coords = observer_point_coords + np.array([np.cos(i), np.sin(i)]) * ray_length
        direction_line = LineString([observer_point_coords, shifted_point_coords])
        # direction = get_clock_angle(Vector(*(shifted_point_coords - observer_point_coords)))
        points = []
        for building in buildings:
            if building.intersects(direction_line):
                intersection = building.intersection(direction_line)
                _, closest_point = nearest_points(observer_point, intersection)
                points.append((closest_point, building.id, distance(observer_point, closest_point)))
                # if abs(get_clock_angle(Vector.from_points(observer_point, intersection_point)) - direction) < 1:
                #     points.append((intersection_point, building.index))
        if not points:
            angle_map.append((observer_point, None, 0))
            continue
        angle_map.append(min(points, key=lambda x: x[2]))
    encoded_array = rle_encode(list(map(lambda x: x[1], angle_map)))
    iteration_angle = 360 / iterations
    last_angle = 0

    res = []

    for ctr, index in encoded_array:
        avg_distance = mean(list(map(lambda x: x[2], filter(lambda x: x[1] == index, angle_map))))
        next_angle = last_angle + ctr * iteration_angle
        res.append((last_angle, next_angle, index, avg_distance))
        last_angle = next_angle

    if len(res) != 1 and res[-1][2] == res[0][2] and abs(res[-1][1] - res[0][0] - 360) < 1:
        res[0] = (res[-1][0], res[0][1], res[0][2], res[0][3])
        res.pop()
    return res

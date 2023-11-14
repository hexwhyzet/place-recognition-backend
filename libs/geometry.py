import math

from shapely import Point


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @classmethod
    def from_points(cls, p1: Point, p2: Point):
        return cls(p2.x - p1.x, p2.y - p1.y)

    @property
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)


def dot_product(v1: Vector, v2: Vector) -> float:
    return v1.x * v2.x + v1.y * v2.y


def to_degrees(angle) -> float:
    return math.degrees((angle + 2 * math.pi) % (2 * math.pi))


def get_clock_angle(v1: Vector) -> float:
    if v1.y == 0:
        if v1.x >= 0:
            return 90
        else:
            return 270
    return to_degrees(math.atan2(v1.x, v1.y))


def get_directed_angle(v1: Vector, v2: Vector) -> float:
    return get_clock_angle(v2) - get_clock_angle(v1)

from typing import List, Union

from models.geo import Area, CoordinateSystem
from models.image import PathImage


class PathImageFilter:
    def __call__(self, images: Union[PathImage, List[PathImage]]) -> List[PathImage]:
        if isinstance(images, PathImage):
            images = [images]
        return list(filter(lambda image: self.filter(image), images))

    def filter(self, image: PathImage) -> bool:
        raise NotImplementedError


class AreaPathImageFilter(PathImageFilter):
    def __init__(self, area: Area):
        self.area = area

    def filter(self, image: PathImage) -> bool:
        return self.area.contains(image.meta.coordinates.point(CoordinateSystem.PROJECTION))


# class BuildingIntersectionFilter(PathImageFilter):
#     def __init__(self):
#         self.buildings = get_buildings()
#
#     def filter(self, image: PathImage) -> bool:
#         for building in self.buildings:
#             if building.contains(image.meta.coordinates.point(CoordinateSystem.PROJECTION)):
#                 return False
#         return True

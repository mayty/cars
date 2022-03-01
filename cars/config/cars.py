from cars.config.base import ImmutableBaseModel
from typing import Optional, List


class CarConfig(ImmutableBaseModel):
    brand: str
    model: str
    generations: Optional[List[str]]
    body_types: Optional[List[str]]


class CarsConfig(ImmutableBaseModel):
    cars: List[CarConfig]

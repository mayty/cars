from cars.config.base import ImmutableBaseModel
from typing import Optional, List


class CarConfig(ImmutableBaseModel):
    brand: str
    model: str
    generation: Optional[str]


class CarsConfig(ImmutableBaseModel):
    cars: List[CarConfig]

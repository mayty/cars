from pydantic import AnyHttpUrl

from cars.config.base import ImmutableBaseModel


class AppConfig(ImmutableBaseModel):
    host: AnyHttpUrl
    filter_request: str
    models_request: str

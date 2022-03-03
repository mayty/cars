from os import environ
from pathlib import Path
import yaml

from cars.config.app import AppConfig
from cars.config.cars import CarsConfig

config_root = environ.get("CONFIG_PATH", "config/")

_config_path = Path(f"{config_root}config.yaml").expanduser()
_cars_path = Path(f"{config_root}cars.yaml").expanduser()

_config_mapping = yaml.full_load(_config_path.read_text(encoding="utf-8"))
_cars_config_mapping = yaml.full_load(_cars_path.read_text(encoding="utf-8"))

app_config = AppConfig(**_config_mapping)
cars_config = CarsConfig(**_cars_config_mapping)

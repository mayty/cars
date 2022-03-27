import re
from typing import Tuple, Optional, Dict, List, Iterable

from requests import get, post

from cars.common import classproperty
from cars.config import app_config
from cars.exceptions import ApiRequestError, InvalidVendor, InvalidModel, InvalidGeneration

CarDataT = Tuple[int, int, str, int, str]


def init_basic_metadata() -> None:
    response = get("https://cars.av.by/")
    if response.status_code != 200:
        raise ApiRequestError(f"Models Request Fail: {response.status_code}, {response.reason}")
    data = response.content.decode()
    VendorsMetadata.init_mapping(data)
    BodyMetadata.init_mapping(data)


class GenerationsMetadata:
    def __init__(self, vendor_id: int, model_id: int) -> None:
        url = app_config.host + app_config.models_request
        payload = {
            "properties": [
                {
                    "modified": True,
                    "name": "brands",
                    "property": 1440,
                    "value": [
                        [
                            {
                                "name": "brand",
                                "value": vendor_id,
                            },
                            {
                                "name": "model",
                                "value": model_id,
                                "modified": True,
                                "previousValue": None,
                            },
                        ],
                    ],
                },
                {
                    "name": "price_currency",
                    "value": 2,
                },
            ],
        }
        response = post(
            url,
            json=payload,
        )

        if response.status_code != 200:
            raise ApiRequestError(f"Request error: {response.status_code}, {response.reason}")

        response_data = response.json()
        self._generations_data = {
            model["label"]: model["intValue"] for model in response_data["properties"][0]["value"][0][3]["options"]
        }

    def get_generation_id(self, generation: str) -> int:
        if generation not in self._generations_data:
            raise InvalidGeneration(
                f"Generation {generation} not found. "
                f"Must be one of {[key for key in self._generations_data.keys()]}."
            )
        return self._generations_data[generation]


class ModelsMetadata:
    def __init__(self, vendor_id: int) -> None:
        url = app_config.host + app_config.models_request
        payload = {
            "properties": [
                {
                    "modified": True,
                    "name": "brands",
                    "property": 1440,
                    "value": [[{"name": "brand", "value": vendor_id, "modified": True, "previousValue": None}]],
                },
                {"name": "price_currency", "value": 2},
            ]
        }
        response = post(
            url,
            json=payload,
        )

        if response.status_code != 200:
            raise ApiRequestError(f"Request error: {response.status_code}, {response.reason}")

        response_data = response.json()
        self._models_data = {
            model["label"]: model["intValue"] for model in response_data["properties"][0]["value"][0][2]["options"]
        }

    def get_model_id(self, model: str) -> int:
        if model not in self._models_data:
            raise InvalidModel(
                f"Model {model} not found. " f"Must be one of {[key for key in self._models_data.keys()]}."
            )
        return self._models_data[model]


class VendorsMetadata:
    _ID_MAPPING: Optional[Dict[str, int]] = None
    _MODELS_MAPPING: Dict[int, ModelsMetadata] = {}
    _GENERATIONS_MAPPING: Dict[Tuple[int, int], GenerationsMetadata] = {}

    @classmethod
    def init_mapping(cls, data: str) -> None:
        names_matches = re.findall(
            pattern=r'(data-property-name="brand">)(.*?)(</button>)',
            string=data,
        )

        names = set(name[1] for name in names_matches)

        VendorsMetadata._ID_MAPPING = {}
        for name in names:
            name_fixed = name.replace("(", "\(")
            name_fixed = name_fixed.replace(")", "\)")
            id_matches = re.findall(
                pattern=f'("id":)([0-9]*?)(,"label":"{name_fixed}")',
                string=data,
            )
            ids = set(_id[1] for _id in id_matches)
            if len(ids) != 1:
                print(f"Ambiguous id: {name} - {ids}")
                continue
            VendorsMetadata._ID_MAPPING[name] = int(ids.pop())

        assert VendorsMetadata._ID_MAPPING is not None

    @classproperty
    def id_mapping(cls) -> Dict[str, int]:
        if VendorsMetadata._ID_MAPPING is None:
            init_basic_metadata()
        assert VendorsMetadata._ID_MAPPING is not None
        return VendorsMetadata._ID_MAPPING

    @classmethod
    def get_models(cls, vendor: str) -> ModelsMetadata:
        vendor_id = cls.get_id(vendor)
        if vendor_id not in cls._MODELS_MAPPING:
            models_data = ModelsMetadata(vendor_id)
            cls._MODELS_MAPPING[vendor_id] = models_data
        return cls._MODELS_MAPPING[vendor_id]

    @classmethod
    def get_model_id(cls, vendor: str, model: str) -> int:
        models_metadata = cls.get_models(vendor)
        return models_metadata.get_model_id(model)

    @classmethod
    def get_generations(cls, vendor, model) -> GenerationsMetadata:
        vendor_id = cls.get_id(vendor)
        model_id = cls.get_model_id(vendor, model)
        if (vendor_id, model_id) not in cls._GENERATIONS_MAPPING:
            cls._GENERATIONS_MAPPING[(vendor_id, model_id)] = GenerationsMetadata(vendor_id, model_id)
        return cls._GENERATIONS_MAPPING[(vendor_id, model_id)]

    @classmethod
    def get_generation_id(cls, vendor, model, generation) -> int:
        generations_metadata = cls.get_generations(vendor, model)
        return generations_metadata.get_generation_id(generation)

    @classmethod
    def get_id(cls, vendor: str) -> int:
        if vendor not in cls.id_mapping:
            raise InvalidVendor(
                f"Brand {vendor} not found. " f"Must be one of {[key for key in cls.id_mapping.keys()]}."
            )
        return cls.id_mapping[vendor]


class BodyMetadata:
    _ID_MAPPING: Optional[Dict[str, int]] = None

    @classmethod
    def init_mapping(cls, data: str) -> None:
        body_type_matches = re.findall(
            pattern=r'("body_type":\{.*?"options":\[)(.*?)(\].*?\})',
            string=data,
        )
        body_types_str = body_type_matches[0][1]
        BodyMetadata._ID_MAPPING = {}
        for match in re.findall(
            pattern=r"\{.*?\}",
            string=body_types_str,
        ):
            int_value = int(
                re.findall(pattern='("intValue":)([0-9]*)', string=match,)[
                    0
                ][1]
            )
            name = re.findall(pattern='("label":")(.*?)(")', string=match,)[
                0
            ][1]
            BodyMetadata._ID_MAPPING[name] = int_value

    @classproperty
    def id_mapping(cls) -> Dict[str, int]:
        if BodyMetadata._ID_MAPPING is None:
            init_basic_metadata()
        assert BodyMetadata._ID_MAPPING is not None
        return BodyMetadata._ID_MAPPING

    @classmethod
    def get_id(cls, body_type: str) -> int:
        if body_type not in cls.id_mapping:
            raise InvalidVendor(
                f"Body type {body_type} not found. " f"Must be one of {[key for key in cls.id_mapping.keys()]}."
            )
        return cls.id_mapping[body_type]


class CarsParser:
    def __init__(self, vendor: str, model: str, revision: Optional[str], body_types: Optional[Iterable[str]]) -> None:
        self.brand: str = vendor
        self.brand_id: int = VendorsMetadata.get_id(self.brand)
        self.model: str = model
        self.model_id: int = VendorsMetadata.get_models(self.brand).get_model_id(self.model)
        self.body_type_ids: List[int] = (
            [BodyMetadata.get_id(body_type) for body_type in body_types] if body_types else []
        )
        self.generation: Optional[str] = revision if revision else None
        self._car_data: Optional[List[CarDataT]] = None

    @property
    def car_data(self) -> List[CarDataT]:
        if self._car_data is None:
            self._car_data = self._get_car_data()
        assert self._car_data is not None
        return self._car_data

    @classproperty
    def columns_order(self) -> Tuple[str, ...]:
        return "цена", "год выпуска", "ссылка", "дней в продаже", "тип кузова"

    @classmethod
    def render_car_data(cls, data: CarDataT) -> str:
        return "\t".join((str(data[0]), str(data[1]), data[2]))

    def _get_page_data(self, page_id) -> Tuple[List[CarDataT], Optional[int]]:
        print(page_id, end="")
        url = app_config.host + app_config.filter_request
        payload = {
            "page": page_id,
            "properties": [
                {
                    "modified": True,
                    "name": "brands",
                    "property": 1440,
                    "value": [
                        [
                            {
                                "name": "brand",
                                "value": self.brand_id,
                            },
                            {
                                "name": "model",
                                "value": self.model_id,
                            },
                        ],
                    ],
                },
                {
                    "name": "price_currency",
                    "value": 2,
                },
                {
                    "name": "transmission_type",
                    "value": 2,
                },
            ],
        }

        if self.generation is not None:
            payload["properties"][0]["value"][0].append(  # type: ignore
                {
                    "name": "generation",
                    "value": VendorsMetadata.get_generation_id(self.brand, self.model, self.generation),
                }
            )

        if self.body_type_ids:
            payload["properties"].append(
                {  # type: ignore
                    "name": "body_type",
                    "value": self.body_type_ids,
                }
            )

        response = post(
            url,
            json=payload,
        )

        if response.status_code != 200:
            raise ApiRequestError(f"Request error: {response.status_code}, {response.reason}")

        response_data = response.json()
        result = []

        page_count = response_data["pageCount"]
        next_page_id = None if page_id >= page_count else (page_id + 1)
        print(f"/{page_count}")

        for ad in response_data["adverts"]:
            body_type = "-"
            for _property in ad["properties"]:
                if _property["name"] == "body_type":
                    body_type = _property["value"]
                    break
            result.append(
                (ad["price"]["usd"]["amount"], ad["year"], ad["publicUrl"], ad["originalDaysOnSale"], body_type),
            )

        return result, next_page_id

    def _get_car_data(self) -> List[CarDataT]:
        result = []

        next_page_id: Optional[int] = 1
        while next_page_id is not None:
            new_data, next_page_id = self._get_page_data(next_page_id)
            result.extend(new_data)

        return result

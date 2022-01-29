from typing import Tuple, Dict, Any, Generator

from cars.exceptions import InvalidConstantValue


class ConstantsMeta(type):

    dict_field = "__constants_extra__"

    def __new__(mcs, name: str, bases: Tuple, attrs: Dict) -> "ConstantsMeta":
        values = [value for key, value in attrs.items() if not key.startswith("_")]
        if len(values) != len(set(values)):
            raise ValueError(f"Values in constants class are not unique: {values}")

        attrs[ConstantsMeta.dict_field] = {"all": set(values)}
        return super().__new__(mcs, name, bases, attrs)

    def __init__(cls, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        constants_extra = getattr(cls, ConstantsMeta.dict_field, {})
        cls.ALL = constants_extra.get("all", set())

    def __instancecheck__(self, instance: Any) -> bool:
        return instance in self.ALL

    def __contains__(self, item: Any) -> bool:
        return item in self.ALL

    def __iter__(self) -> Generator:
        return (value for value in self.ALL)

    def __get_validators__(cls) -> Generator:
        for func in (
            cls.cast,
            cls.validate,
        ):
            yield func

    def cast(cls, v: Any) -> Any:
        return cls(v)

    def validate(cls, v: Any) -> Any:
        if v not in cls.ALL:
            raise InvalidConstantValue(f'Invalid value "{v}". Value must be one of {cls.ALL}')
        return v

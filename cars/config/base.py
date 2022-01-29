from pydantic.main import BaseModel


class ImmutableBaseModel(BaseModel):
    class Config:
        allow_mutation = False
        extra = "forbid"

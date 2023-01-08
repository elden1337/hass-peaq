from dataclasses import dataclass


@dataclass(frozen=False)
class EntitiesPostModel:
    domain: str = None
    entityschema: str = None
    endings: list = None

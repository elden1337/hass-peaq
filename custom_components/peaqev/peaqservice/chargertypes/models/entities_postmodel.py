from dataclasses import dataclass

@dataclass
class EntitiesPostModel:
    domain: str = None
    entityschema: str = None
    endings: list = None
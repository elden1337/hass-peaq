from dataclasses import dataclass, field


@dataclass
class EntitiesModel:
    entityschema: str = ""
    imported_entities: list = field(default_factory=lambda: [])
    valid: bool = False
    

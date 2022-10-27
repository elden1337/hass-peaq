import logging
from dataclasses import dataclass

# from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import entity_sources

_LOGGER = logging.getLogger(__name__)


@dataclass
class EntitiesPostModel:
    domain: str = None
    entityschema: str = None
    endings: list = None


@dataclass
class EntitiesModel:
    entityschema: str
    imported_entities: list


def get_entities(hass,
                 model: EntitiesPostModel,
                 ) -> EntitiesModel:
    if len(model.entityschema) < 1:
        entities = get_entities_from_hass(hass, model.domain)
        if len(entities) < 1:
            _LOGGER.error(f"no entities found for {model.domain}")
        else:
            candidate = ""
            for e in entities:
                splitted = e.split(".")
                for ending in model.endings:
                    if splitted[1].endswith(ending):
                        candidate = splitted[1].replace(ending, '')
                        break
                if len(candidate) > 1:
                    break
            return EntitiesModel(entityschema=candidate, imported_entities=entities)


def get_entities_from_hass(hass, domain_name) -> list:
    return [
        entity_id
        for entity_id, info in entity_sources(hass).items()
        if info["domain"] == domain_name
           or info["domain"] == domain_name.capitalize()
           or info["domain"] == domain_name.upper()
           or info["domain"] == domain_name.lower()
    ]

# def get_device_id_from_hass(hass, sensor):
#     try:
#         entity_reg = er.async_get(hass)
#         entry = entity_reg.async_get(sensor)
#         _LOGGER.debug(f"Device-id for {sensor} is: {entry.device_id}")
#         return str(entry.device_id)
#     except Exception as e:
#         _LOGGER.debug(f"Could not get device-id for {sensor}: {e}")
#         return None

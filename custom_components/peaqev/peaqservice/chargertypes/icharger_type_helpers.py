import logging
import time
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import entity_sources
from custom_components.peaqev.peaqservice.chargertypes.models.entities_model import EntitiesModel


_LOGGER = logging.getLogger(__name__)


def check_required_sensors(required_types: list, sensors: dict) -> bool:
        for required in required_types:
            try:
                assert required in sensors.keys()
            except AssertionError as a:
                _LOGGER.error(f"could not find the required sensor {required} in the set sensors")
                return False
        return True


def set_entitiesmodel(hass: HomeAssistant, domain:str, entity_endings:list, entity_schema:str) -> EntitiesModel:
    if len(entity_schema) < 1:
        entities = get_entities_from_hass(hass=hass, domain_name=domain)

        if len(entities) < 1:
            _LOGGER.error(f"no entities found for {domain} at {time.time()}")
        else:
            candidate = ""
            for e in entities:
                splitted = e.split(".")
                for ending in entity_endings:
                    if splitted[1].endswith(ending):
                        candidate = splitted[1].replace(ending, '')
                        break
                if len(candidate) > 1:
                    break
            _LOGGER.debug(f"entityschema is: {candidate}")
            return EntitiesModel(entityschema=candidate, imported_entities=entities)


def get_entities_from_hass(hass: HomeAssistant, domain_name: str) -> list:
    try:
        return [
            entity_id
            for entity_id, info in entity_sources(hass).items()
            if info["domain"] == domain_name
               or info["domain"] == domain_name.capitalize()
               or info["domain"] == domain_name.upper()
               or info["domain"] == domain_name.lower()
        ]
    except Exception as e:
        _LOGGER.exception(f"Could not get charger-entities from Home Assistant: {e}")
        return []

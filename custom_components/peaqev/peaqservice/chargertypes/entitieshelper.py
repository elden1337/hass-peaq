import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import entity_sources

from custom_components.peaqev.peaqservice.chargertypes.models.entities_model import EntitiesModel
from custom_components.peaqev.peaqservice.chargertypes.models.entities_postmodel import EntitiesPostModel

_LOGGER = logging.getLogger(__name__)


def set_entitiesmodel(hass: HomeAssistant,
                      model: EntitiesPostModel,
                      ) -> EntitiesModel:
    if len(model.entityschema) < 1:
        entities = get_entities_from_hass(hass=hass, domain_name=model.domain)

        if len(entities) < 1:
            _LOGGER.error(f"no entities found for {model.domain} at {time.time()}")
        else:
            # _endings = model.endings
            candidate = ""

            for e in entities:
                splitted = e.split(".")
                for ending in model.endings:
                    if splitted[1].endswith(ending):
                        candidate = splitted[1].replace(ending, '')
                        break
                if len(candidate) > 1:
                    break

            _LOGGER.debug(f"entityschema is: {candidate} at {time.time()}")
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

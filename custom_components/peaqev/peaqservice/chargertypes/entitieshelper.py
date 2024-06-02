import logging
import time

from custom_components.peaqev.peaqservice.chargertypes.models.entities_model import EntitiesModel
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade

_LOGGER = logging.getLogger(__name__)


def set_entitiesmodel(
    hass: IHomeAssistantFacade, domain: str, entity_endings: list, entity_schema: str
) -> EntitiesModel:
    if len(entity_schema) < 1:
        entities = get_entities_from_hass(hass=hass, domain_name=domain)
        if len(entities) < 1:
            _LOGGER.error(f'no entities found for {domain} at {time.time()}')
        else:
            candidate = ''
            for e in entities:
                splitted = e.split('.')
                for ending in entity_endings:
                    if splitted[1].endswith(ending):
                        candidate = splitted[1].replace(ending, '')
                        break
                if len(candidate) > 1:
                    break
            _LOGGER.debug(f'entityschema is: {candidate} at {time.time()}')
            return EntitiesModel(
                entityschema=candidate, imported_entities=entities, valid=True
            )
    return EntitiesModel()


def get_entities_from_hass(hass: IHomeAssistantFacade, domain_name: str) -> list:
    try:
        return [
            entity_id
            for entity_id, info in hass.entity_sources.items()
            if info['domain'] == domain_name
            or info['domain'] == domain_name.capitalize()
            or info['domain'] == domain_name.upper()
            or info['domain'] == domain_name.lower()
        ]
    except Exception as e:
        _LOGGER.exception(f'Could not get charger-entities from Home Assistant: {e}')
        return []

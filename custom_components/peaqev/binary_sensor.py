import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from custom_components.peaqev.sensors.peaq_binary_sensor import PeaqBinarySensorDone
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):  # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = await _gather_binary_sensors(hub)
    async_add_entities(peaqsensors)

SCAN_INTERVAL = timedelta(seconds=4)


async def _gather_binary_sensors(hub) -> list:
    ret = []
    if hub.chargertype.type != ChargerType.NoCharger:
        ret.append(PeaqBinarySensorDone(hub))
    return ret
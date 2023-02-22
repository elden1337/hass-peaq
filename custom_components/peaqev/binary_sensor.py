import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant

import custom_components.peaqev.sensors.create_sensor_helper as helper
from custom_components.peaqev.const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):  # pylint:disable=unused-argument
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = helper.gather_binary_sensors(hub)
    async_add_entities(peaqsensors)

SCAN_INTERVAL = timedelta(seconds=4)



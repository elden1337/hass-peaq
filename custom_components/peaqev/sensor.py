"""Platform for sensor integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
import custom_components.peaqev.sensors.create_sensor_helper as _helper
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME,
    CONSUMPTION_INTEGRAL_NAME
)
from custom_components.peaqev.sensors.utility_sensor import (
    PeaqUtilitySensor,
    METER_OFFSET
)
from .const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=4)

async def async_setup_entry(hass : HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = await _helper.gather_Sensors(hub, config)
    async_add_entities(peaqsensors, update_before_add = True)

    peaqintegrationsensors = await _helper.gather_integration_sensors(hub, config.entry_id)

    async_add_entities(peaqintegrationsensors, update_before_add=True)

    integrationsensors = [ex.nametoid(CONSUMPTION_TOTAL_NAME), ex.nametoid(CONSUMPTION_INTEGRAL_NAME)]
    peaqutilitysensors = []

    for i in integrationsensors:
        peaqutilitysensors.append(PeaqUtilitySensor(hub, i, hub.locale.data.peak_cycle, METER_OFFSET, config.entry_id))

    async_add_entities(peaqutilitysensors, update_before_add = True)

    peaqsqlsensors = await _helper.gather_sql_sensors(hass, hub, config.entry_id)

    async_add_entities(peaqsqlsensors, update_before_add = True)

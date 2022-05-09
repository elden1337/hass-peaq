"""Platform for sensor integration."""
import logging
from custom_components.peaqev.sensors.utility_sensor import (
    PeaqUtilitySensor,
    METER_OFFSET,
    PERIODS
)

import custom_components.peaqev.sensors.create_sensor_helper as _helper
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME,
    CONSUMPTION_INTEGRAL_NAME
    )

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta

from .const import (
    DOMAIN)
from .sensors.money_sensor import PeaqMoneySensor

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=4)

async def async_setup_entry(hass : HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = await _helper.gather_Sensors(hub, config.entry_id)
    async_add_entities(peaqsensors, update_before_add = True)

    peaqintegrationsensors = await _helper.gather_integration_sensors(hub, config.entry_id)

    async_add_entities(peaqintegrationsensors, update_before_add=True)

    integrationsensors = [ex.nametoid(CONSUMPTION_TOTAL_NAME), ex.nametoid(CONSUMPTION_INTEGRAL_NAME)]
    peaqutilitysensors = []

    for i in integrationsensors:
        for p in PERIODS:
            peaqutilitysensors.append(PeaqUtilitySensor(hub, i, p, METER_OFFSET, config.entry_id))
    
    async_add_entities(peaqutilitysensors, update_before_add = True)

    peaqsqlsensors = await _helper.gather_sql_sensors(hass, hub, config.entry_id)

    async_add_entities(peaqsqlsensors, update_before_add = True)

    if hub.price_aware is True:
        moneysensors = []
        moneysensors.append(PeaqMoneySensor(hub, config.entry_id))
        async_add_entities(moneysensors, update_before_add=True)


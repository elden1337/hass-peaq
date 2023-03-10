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
from custom_components.peaqev.sensors.sql_sensor import PeaqPeakSensor
from custom_components.peaqev.sensors.utility_sensor import (
    PeaqUtilitySensor,
    METER_OFFSET, PeaqUtilityCostSensor
)
from .const import (
    DOMAIN)
from .peaqservice.chargertypes.models.chargertypes_enum import ChargerType

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=4)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = await _helper.gather_sensors(hub, config)
    async_add_entities(peaqsensors, update_before_add=True)

    peaqintegrationsensors = await _helper.gather_integration_sensors(hub, config.entry_id)

    async_add_entities(peaqintegrationsensors, update_before_add=True)

    integrationsensors = []
    if not hub.options.peaqev_lite: integrationsensors.append(ex.nametoid(CONSUMPTION_TOTAL_NAME))
    if hub.chargertype.type is not ChargerType.NoCharger: integrationsensors.append(ex.nametoid(CONSUMPTION_INTEGRAL_NAME))
    peaqutilitysensors = []

    for i in integrationsensors:
        peaqutilitysensors.append(PeaqUtilitySensor(hub, i, hub.sensors.locale.data.peak_cycle, METER_OFFSET, config.entry_id))
    if not hub.options.peaqev_lite: 
        peaqutilitysensors.append(PeaqUtilityCostSensor(hub, f"sensor.{DOMAIN}_wattage_cost", "daily", METER_OFFSET, config.entry_id))
        peaqutilitysensors.append(PeaqUtilityCostSensor(hub, f"sensor.{DOMAIN}_wattage_cost", "monthly", METER_OFFSET, config.entry_id))

    async_add_entities(peaqutilitysensors, update_before_add=True)

    if hub.chargertype.type is not ChargerType.NoCharger:
        peaksensor = [PeaqPeakSensor(hub, config.entry_id)]
        async_add_entities(peaksensor, update_before_add=True)


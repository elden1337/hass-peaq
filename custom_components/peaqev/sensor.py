"""Platform for sensor integration."""
import logging
from datetime import timedelta
from peaqevcore.models.hub.const import AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import (
    DOMAIN)
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME,
    CONSUMPTION_INTEGRAL_NAME
)
from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
from custom_components.peaqev.sensors.integration_sensor import PeaqIntegrationSensor, PeaqIntegrationCostSensor
from custom_components.peaqev.sensors.money_sensor import PeaqMoneySensor

from custom_components.peaqev.sensors.peaq_sensor import PeaqSensor
from custom_components.peaqev.sensors.power_sensor import (
    PeaqPowerSensor, 
    PeaqAmpSensor, 
    PeaqHousePowerSensor,
    PeaqPowerCostSensor)
from custom_components.peaqev.sensors.powercanary_sensor import (
    PowerCanaryStatusSensor, 
    PowerCanaryPercentageSensor,
    PowerCanaryMaxAmpSensor)
from custom_components.peaqev.sensors.prediction_sensor import PeaqPredictionSensor
from custom_components.peaqev.sensors.session_sensor import PeaqSessionSensor, PeaqSessionCostSensor
from custom_components.peaqev.sensors.threshold_sensor import PeaqThresholdSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.utility_meter.const import QUARTER_HOURLY, DAILY, MONTHLY
from peaqevcore.models.locale.enums.time_periods import TimePeriods
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.util.constants import (CONSUMPTION_TOTAL_NAME, CONSUMPTION_INTEGRAL_NAME)
from custom_components.peaqev.sensors.sql_sensor import PeaqPeakSensor
from custom_components.peaqev.sensors.utility_sensor import (
    PeaqUtilitySensor, 
    PeaqUtilityCostSensor, 
    METER_OFFSET
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=4)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]
    await _gather_all_sensors(hub, config, async_add_entities)

async def _gather_all_sensors(hub, config, async_add_entities) -> None:
    async_add_entities(await _gather_sensors(hub, config), update_before_add=True)
    async_add_entities(await _gather_integration_sensors(hub, config.entry_id), update_before_add=True)

    integrationsensors = []
    if not hub.options.peaqev_lite:
        integrationsensors.append(ex.nametoid(CONSUMPTION_TOTAL_NAME))
    if hub.chargertype.type is not ChargerType.NoCharger:
        integrationsensors.append(ex.nametoid(CONSUMPTION_INTEGRAL_NAME))

    async_add_entities(await _gather_utility_sensors(hub, config, integrationsensors), update_before_add=True)
    async_add_entities(await _setup_extra_utilities(hub, config), update_before_add=True)

    if hub.chargertype.type is not ChargerType.NoCharger:
        async_add_entities([PeaqPeakSensor(hub, config.entry_id)], update_before_add=True)

async def _gather_utility_sensors(hub, config, integrationsensors):
    ret = []
    for i in integrationsensors:
        ret.append(PeaqUtilitySensor(hub, i, hub.sensors.locale.data.peak_cycle, METER_OFFSET, config.entry_id))
        if all([
            i == ex.nametoid(CONSUMPTION_TOTAL_NAME),
            hub.options.peaqev_lite is False,
            hub.options.price.price_aware is True
        ]):
            ret.append(PeaqUtilitySensor(hub, i, TimePeriods.Daily, METER_OFFSET, config.entry_id))
            ret.append(PeaqUtilitySensor(hub, i, TimePeriods.Monthly, METER_OFFSET, config.entry_id))
    return ret

async def _setup_extra_utilities(hub, config):
    ret = []
    if not hub.options.peaqev_lite and hub.options.price.price_aware:
        energy_cost = "energy_cost_integral"
        ret.append(PeaqUtilityCostSensor(hub, energy_cost, QUARTER_HOURLY, METER_OFFSET, config.entry_id))
        ret.append(PeaqUtilityCostSensor(hub, energy_cost, DAILY, METER_OFFSET, config.entry_id))
        ret.append(PeaqUtilityCostSensor(hub, energy_cost, MONTHLY, METER_OFFSET, config.entry_id))
    return ret

async def _gather_sensors(hub, config) -> list:
    ret = [PeaqSensor(hub, config.entry_id)]

    if hub.chargertype.type is not ChargerType.NoCharger:
        ret.append(PeaqSessionSensor(hub, config.entry_id))
        ret.append(PeaqAmpSensor(hub, config.entry_id))

    if hub.options.peaqev_lite is False:
        if hub.options.powersensor_includes_car or hub.chargertype.type is ChargerType.NoCharger:
            ret.append(PeaqHousePowerSensor(hub, config.entry_id))
        else:
            ret.append(PeaqPowerSensor(hub, config.entry_id))
        average_delta = 2 if hub.sensors.locale.data.is_quarterly(hub.sensors.locale.data) else 5
        ret.append(PeaqAverageSensor(hub, config.entry_id, AVERAGECONSUMPTION, timedelta(minutes=average_delta)))
        ret.append(PeaqAverageSensor(hub, config.entry_id, AVERAGECONSUMPTION_24H, timedelta(hours=24)))
        ret.append(PeaqPredictionSensor(hub, config.entry_id))
        ret.append(PeaqThresholdSensor(hub, config.entry_id))

    if hub.power_canary.enabled:
        ret.append(PowerCanaryStatusSensor(hub, config.entry_id))
        ret.append(PowerCanaryPercentageSensor(hub, config.entry_id))
        ret.append(PowerCanaryMaxAmpSensor(hub, config.entry_id, 1))
        ret.append(PowerCanaryMaxAmpSensor(hub, config.entry_id, 3))

    if hub.options.price.price_aware:
        ret.append(PeaqMoneySensor(hub, config.entry_id))
        ret.append(PeaqPowerCostSensor(hub, config.entry_id))
        if hub.chargertype.type != ChargerType.NoCharger:
            ret.append(PeaqSessionCostSensor(hub, config.entry_id))
    return ret

async def _gather_integration_sensors(hub, entry_id):
    ret = []
    if hub.options.peaqev_lite:
        return ret

    if any(
            [
                hub.options.powersensor_includes_car,
                hub.chargertype.type is ChargerType.NoCharger,
            ]):
        if hub.chargertype.type is not ChargerType.NoCharger:
            ret.append(
                PeaqIntegrationSensor(
                    hub=hub,
                    sensor=f"sensor.{DOMAIN}_{hub.sensors.power.house.id}",
                    name=f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                    entry_id=entry_id
                )
            )
        ret.append(
            PeaqIntegrationSensor(
                hub=hub,
                sensor=hub.sensors.power.total.entity,
                name=f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id=entry_id
            )
        )
    else:
        ret.append(
            PeaqIntegrationSensor(
                hub=hub,
                sensor=hub.sensors.power.house.entity,
                name=f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                entry_id=entry_id
            )
        )
        ret.append(
            PeaqIntegrationSensor(
                hub=hub,
                sensor=f"sensor.{DOMAIN}_{hub.sensors.power.total.id}",
                name=f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id=entry_id
            )
        )
    if hub.options.price.price_aware:
        ret.append(
            PeaqIntegrationCostSensor(
                    hub=hub,
                    name="energy_cost_integral",
                    entry_id=entry_id
                )
        )
    return ret
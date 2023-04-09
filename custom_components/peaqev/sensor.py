"""Platform for sensor integration."""
import logging
from datetime import timedelta

import homeassistant.helpers.entity_registry as er
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import HomeAssistant
from peaqevcore.models.hub.const import (AVERAGECONSUMPTION,
                                         AVERAGECONSUMPTION_24H)
from peaqevcore.models.locale.enums.time_periods import TimePeriods

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.const import DOMAIN
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_INTEGRAL_NAME, CONSUMPTION_TOTAL_NAME)
from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
from custom_components.peaqev.sensors.gain_loss_sensor import GainLossSensor
from custom_components.peaqev.sensors.integration_sensor import (
    PeaqIntegrationCostSensor, PeaqIntegrationSensor)
from custom_components.peaqev.sensors.money_sensor import PeaqMoneySensor
from custom_components.peaqev.sensors.peaq_sensor import PeaqSensor
from custom_components.peaqev.sensors.power.amp_sensor import PeaqAmpSensor
from custom_components.peaqev.sensors.power.power_cost_sensor import \
    PeaqPowerCostSensor
from custom_components.peaqev.sensors.power.power_house_sensor import \
    PeaqHousePowerSensor
from custom_components.peaqev.sensors.power.power_sensor import PeaqPowerSensor
from custom_components.peaqev.sensors.power.powercanary_sensor import (
    PowerCanaryMaxAmpSensor, PowerCanaryPercentageSensor,
    PowerCanaryStatusSensor)
from custom_components.peaqev.sensors.prediction_sensor import \
    PeaqPredictionSensor
from custom_components.peaqev.sensors.session_sensor import (
    PeaqSessionCostSensor, PeaqSessionSensor)
from custom_components.peaqev.sensors.sql_sensor import PeaqPeakSensor
from custom_components.peaqev.sensors.threshold_sensor import \
    PeaqThresholdSensor
from custom_components.peaqev.sensors.utility_sensor import (PeaqUtilitySensor,
                                                             UtilityMeterDTO)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=4)
ENERGY_COST_INTEGRAL = "energy_cost_integral"


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]
    hass.async_create_task(async_setup(hub, config, hass, async_add_entities))


async def async_setup_utility_meters(hub, hass, utility_meters: list) -> list:
    ret = []
    for meter in utility_meters:
        ret.append(
            PeaqUtilitySensor(
                hub, hass, meter.sensor, meter.meter_type, meter.entry_id, meter.visible_default
            )
        )

    entity_registry = er.async_get(hass)
    for r in ret:
        existing_entity_id = entity_registry.async_get_entity_id(
            domain="sensor", platform=DOMAIN, unique_id=r.unique_id
        )
        if existing_entity_id and hass.states.get(existing_entity_id):
            _LOGGER.debug(f"already found {r} in er. removing from setup.")
            ret.remove(r)

    return ret


async def async_setup(hub, config, hass, async_add_entities):
    integrationsensors = []
    utility_meters = []
    integration_sensors = []
    ret = [PeaqSensor(hub, config.entry_id)]

    if all(
        [
            hub.options.gainloss,
            hub.options.price.price_aware,
            hub.options.peaqev_lite is False,
        ]
    ):
        """implement gainloss sensors"""
        ret.append(GainLossSensor(hub, config.entry_id, TimePeriods.Daily))
        ret.append(GainLossSensor(hub, config.entry_id, TimePeriods.Monthly))
        ret.append(PeaqPowerCostSensor(hub, config.entry_id))
        ret.append(PeaqIntegrationCostSensor(hub, ENERGY_COST_INTEGRAL, config.entry_id))
        utility_meters.append(
            UtilityMeterDTO(
                visible_default=False,
                sensor=ENERGY_COST_INTEGRAL,
                meter_type=TimePeriods.Daily,
                entry_id=config.entry_id,
            )
        )
        utility_meters.append(
            UtilityMeterDTO(
                visible_default=False,
                sensor=ENERGY_COST_INTEGRAL,
                meter_type=TimePeriods.Monthly,
                entry_id=config.entry_id,
            )
        )

    if hub.options.price.price_aware:
        ret.append(PeaqMoneySensor(hub, config.entry_id))
        if hub.chargertype.type != ChargerType.NoCharger:
            ret.append(PeaqSessionCostSensor(hub, config.entry_id))
        if not hub.options.peaqev_lite:
            utility_meters.append(
                UtilityMeterDTO(
                    visible_default=False,
                    sensor=ex.nametoid(CONSUMPTION_TOTAL_NAME),
                    meter_type=TimePeriods.Daily,
                    entry_id=config.entry_id,
                )
            )
            utility_meters.append(
                UtilityMeterDTO(
                    visible_default=False,
                    sensor=ex.nametoid(CONSUMPTION_TOTAL_NAME),
                    meter_type=TimePeriods.Monthly,
                    entry_id=config.entry_id,
                )
            )

    if not hub.options.peaqev_lite:
        integrationsensors.append(ex.nametoid(CONSUMPTION_TOTAL_NAME))
        if hub.options.powersensor_includes_car or hub.chargertype.type is ChargerType.NoCharger:
            ret.append(PeaqHousePowerSensor(hub, config.entry_id))
        else:
            ret.append(PeaqPowerSensor(hub, config.entry_id))
        average_delta = 2 if hub.sensors.locale.data.is_quarterly(hub.sensors.locale.data) else 5
        ret.append(
            PeaqAverageSensor(
                hub,
                config.entry_id,
                AVERAGECONSUMPTION,
                timedelta(minutes=average_delta),
            )
        )
        ret.append(PeaqAverageSensor(hub, config.entry_id, AVERAGECONSUMPTION_24H, timedelta(hours=24)))
        ret.append(PeaqPredictionSensor(hub, config.entry_id))
        ret.append(PeaqThresholdSensor(hub, config.entry_id))

        if any(
            [
                hub.options.powersensor_includes_car,
                hub.chargertype.type is ChargerType.NoCharger,
            ]
        ):
            if hub.chargertype.type is not ChargerType.NoCharger:
                integration_sensors.append(
                    PeaqIntegrationSensor(
                        hub,
                        f"sensor.{DOMAIN}_{hub.sensors.power.house.id}",
                        f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                        config.entry_id,
                    )
                )
            integration_sensors.append(
                PeaqIntegrationSensor(
                    hub,
                    hub.sensors.power.total.entity,
                    f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                    config.entry_id,
                )
            )
        else:
            integration_sensors.append(
                PeaqIntegrationSensor(
                    hub,
                    hub.sensors.power.house.entity,
                    f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                    config.entry_id,
                )
            )
            integration_sensors.append(
                PeaqIntegrationSensor(
                    hub,
                    f"sensor.{DOMAIN}_{hub.sensors.power.total.id}",
                    f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                    config.entry_id,
                )
            )

    if hub.chargertype.type is not ChargerType.NoCharger:
        integrationsensors.append(ex.nametoid(CONSUMPTION_INTEGRAL_NAME))
        ret.append(PeaqSessionSensor(hub, config.entry_id))
        ret.append(PeaqAmpSensor(hub, config.entry_id))
        ret.append(PeaqPeakSensor(hub, config.entry_id))

    if hub.power.power_canary.enabled:
        ret.append(PowerCanaryStatusSensor(hub, config.entry_id))
        ret.append(PowerCanaryPercentageSensor(hub, config.entry_id))
        ret.append(PowerCanaryMaxAmpSensor(hub, config.entry_id, 1))
        ret.append(PowerCanaryMaxAmpSensor(hub, config.entry_id, 3))

    for i in integrationsensors:
        utility_meters.append(
            UtilityMeterDTO(
                visible_default=True,
                sensor=i,
                meter_type=hub.sensors.locale.data.peak_cycle,
                entry_id=config.entry_id,
            )
        )
    async_add_entities(ret)
    async_add_entities(integration_sensors)
    async_add_entities(await async_setup_utility_meters(hub, hass, utility_meters))
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"domain": DOMAIN})

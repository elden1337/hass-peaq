"""Platform for sensor integration."""
import logging
from datetime import timedelta

from homeassistant.components.utility_meter.const import DAILY, MONTHLY
from homeassistant.config_entries import ConfigEntry
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
from custom_components.peaqev.sensors.utility_sensor import (
    METER_OFFSET, PeaqUtilityCostSensor, PeaqUtilitySensor)

# import homeassistant.helpers.entity_registry as er

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=4)
ENERGY_COST_INTEGRAL = "energy_cost_integral"


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    hub = hass.data[DOMAIN]["hub"]
    hass.async_create_task(_async_setup(hub, config, hass, async_add_entities))


async def _async_setup(hub, config, hass, async_add_entities):
    integrationsensors = []
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
        ret.append(
            PeaqUtilityCostSensor(hub, ENERGY_COST_INTEGRAL, DAILY, METER_OFFSET, config.entry_id, hass)
        )
        ret.append(
            PeaqUtilityCostSensor(hub, ENERGY_COST_INTEGRAL, MONTHLY, METER_OFFSET, config.entry_id, hass)
        )

    if hub.options.price.price_aware:
        ret.append(PeaqMoneySensor(hub, config.entry_id))
        if hub.chargertype.type != ChargerType.NoCharger:
            ret.append(PeaqSessionCostSensor(hub, config.entry_id))
        if not hub.options.peaqev_lite:
            ret.append(
                PeaqUtilitySensor(
                    hub,
                    ex.nametoid(CONSUMPTION_TOTAL_NAME),
                    TimePeriods.Daily,
                    METER_OFFSET,
                    config.entry_id,
                    hass,
                )
            )
            ret.append(
                PeaqUtilitySensor(
                    hub,
                    ex.nametoid(CONSUMPTION_TOTAL_NAME),
                    TimePeriods.Monthly,
                    METER_OFFSET,
                    config.entry_id,
                    hass,
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
                ret.append(
                    PeaqIntegrationSensor(
                        hub,
                        f"sensor.{DOMAIN}_{hub.sensors.power.house.id}",
                        f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                        config.entry_id,
                    )
                )
            ret.append(
                PeaqIntegrationSensor(
                    hub,
                    hub.sensors.power.total.entity,
                    f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                    config.entry_id,
                )
            )
        else:
            ret.append(
                PeaqIntegrationSensor(
                    hub,
                    hub.sensors.power.house.entity,
                    f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                    config.entry_id,
                )
            )
            ret.append(
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
        ret.append(
            PeaqUtilitySensor(
                hub,
                i,
                hub.sensors.locale.data.peak_cycle,
                METER_OFFSET,
                config.entry_id,
                hass,
            )
        )

    async_add_entities(ret)

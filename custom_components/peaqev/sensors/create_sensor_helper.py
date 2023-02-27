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
from custom_components.peaqev.sensors.integration_sensor import PeaqIntegrationSensor
from custom_components.peaqev.sensors.money_sensor import PeaqMoneySensor
from custom_components.peaqev.sensors.peaq_binary_sensor import PeaqBinarySensorDone
from custom_components.peaqev.sensors.peaq_sensor import PeaqSensor
from custom_components.peaqev.sensors.power_sensor import (PeaqPowerSensor, PeaqAmpSensor, PeaqHousePowerSensor)
from custom_components.peaqev.sensors.powercanary_sensor import PowerCanaryStatusSensor, PowerCanaryPercentageSensor, \
    PowerCanaryMaxAmpSensor
from custom_components.peaqev.sensors.prediction_sensor import PeaqPredictionSensor
from custom_components.peaqev.sensors.session_sensor import PeaqSessionSensor, PeaqSessionCostSensor
from custom_components.peaqev.sensors.threshold_sensor import PeaqThresholdSensor

_LOGGER = logging.getLogger(__name__)

async def gather_binary_sensors(hub) -> list:

    ret = []
    if hub.chargertype.type != ChargerType.NoCharger:
        ret.append(PeaqBinarySensorDone(hub))
    return ret

async def gather_sensors(hub, config) -> list:
    ret = [PeaqSensor(hub, config.entry_id)]

    if hub.chargertype.type is not ChargerType.NoCharger:
        ret.append(PeaqSessionSensor(hub, config.entry_id))
        ret.append(PeaqAmpSensor(hub, config.entry_id))

    if hub.options.peaqev_lite is False:
        if hub.options.powersensor_includes_car is True or hub.chargertype.type is ChargerType.NoCharger:
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

    if hub.options.price.price_aware is True:
        ret.append(PeaqMoneySensor(hub, config.entry_id))
        if hub.chargertype.type != ChargerType.NoCharger:
            ret.append(PeaqSessionCostSensor(hub, config.entry_id))
    return ret

async def gather_integration_sensors(hub, entry_id):
    ret = []
    if hub.options.peaqev_lite:
        return ret

    if any(
            [
                hub.options.powersensor_includes_car is True,
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
    return ret

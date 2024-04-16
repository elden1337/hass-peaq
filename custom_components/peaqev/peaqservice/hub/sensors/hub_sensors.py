from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial

from peaqevcore.common.average import Average
from peaqevcore.common.trend import Gradient
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power

from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H)
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.sensors.const import *
from custom_components.peaqev.peaqservice.hub.sensors.hub_sensors_base import \
    HubSensorsBase
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


@dataclass
class HubSensors(HubSensorsBase):
    powersensormovingaverage: HubMember = field(init=False)
    powersensormovingaverage24: HubMember = field(init=False)
    power_sensor_moving_average_5: Average = field(init=False)
    power: Power = field(init=False)
    power_trend: Gradient = field(init=False)

    async def async_setup(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        await self.async_setup_base(options, state_machine, domain, chargerobject)

        regular_sensors: dict = {
            POWERSNSRMOVINGAVERAGE_SENSOR: partial(
                HubMember,
                data_type=int,
                listenerentity=f'sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}',
                initval=0,
            ), #not lite
            POWERSNSRMOVINGAVERAGE5_SENSOR: partial(
                Average,
                max_age=300,
                max_samples=300,
                precision=0
            ), #not lite
            POWERSNSRMOVINGAVERAGE24_SENSOR: partial(
                HubMember,
                data_type=int,
                listenerentity=f'sensor.{domain}_{nametoid(AVERAGECONSUMPTION_24H)}',
                initval=0,
            ), #not lite
            POWER_SENSOR: partial(
                Power,
                configsensor=options.powersensor,
                powersensor_includes_car=options.powersensor_includes_car,
            ),
            POWER_TREND_SENSOR: partial(
                Gradient,
                max_age=300,
                max_samples=300,
                precision=0
            ) #not lite
        }

        sensors:dict = {}
        if not options.peaqev_lite:
            sensors.update(regular_sensors)
        self._set_sensors(sensors)

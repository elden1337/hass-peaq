from __future__ import annotations

import time
from dataclasses import dataclass, field
from functools import partial
from statistics import mean
from typing import TYPE_CHECKING, Tuple

from peaqevcore.common.trend import Gradient
from peaqevcore.models.hub.carpowersensor import CarPowerSensor
from peaqevcore.models.hub.chargerobject import ChargerObject
from peaqevcore.models.hub.chargerswitch import ChargerSwitch
from peaqevcore.models.hub.currentpeak import CurrentPeak
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power
from peaqevcore.services.locale.Locale import LocaleData, LocaleFactory

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType

from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H, CHARGER_DONE, CHARGERENABLED,
    CONSUMPTION_TOTAL_NAME, HOURLY)
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


class Average:
    def __init__(self, max_age: int, max_samples: int, precision: int = 2):
        self._readings = []
        self._average = 0
        self._max_age = max_age
        self._max_samples = max_samples
        self._precision = precision
        self._latest_update = 0

    @property
    def average(self) -> float:
        self._set_average()
        return round(self._average, self._precision)

    def _set_average(self):
        try:
            self._average = mean([x[1] for x in self._readings])
        except ZeroDivisionError:
            self._average = 0

    def _remove_from_list(self):
        """Removes overflowing number of samples and old samples from the list."""
        while len(self._readings) > self._max_samples:
            self._readings.pop(0)
        gen = (
            x for x in self._readings if time.time() - int(x[0]) > self._max_age
        )
        for i in gen:
            if len(self._readings) > 1:
                # Always keep one reading
                self._readings.remove(i)

    def add_reading(self, val: float):
        self._readings.append((int(time.time()), round(val, 3)))
        self._latest_update = time.time()
        self._remove_from_list()
        self._set_average()

@dataclass
class HubSensors:
    sensors_list: list[HubMember] = field(init=False)
    charger_enabled: HubMember = field(init=False)
    charger_done: HubMember = field(init=False)
    current_peak: CurrentPeak = field(init=False)
    totalhourlyenergy: HubMember = field(init=False)
    carpowersensor: CarPowerSensor = field(init=False)
    locale: LocaleData = field(init=False)
    chargerobject: ChargerObject = field(init=False)
    chargerobject_switch: ChargerSwitch = field(init=False)
    amp_meter: HubMember = field(init=False)
    state_machine: any = field(init=False)
    powersensormovingaverage: HubMember = field(init=False)
    powersensormovingaverage24: HubMember = field(init=False)
    power_sensor_moving_average_5: Average = field(init=False)
    power: Power = field(init=False)
    power_trend: Gradient = field(init=False)
    chargertype: any = field(init=False)

    async def async_setup(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        self.chargertype: IChargerType = chargerobject
        self.state_machine = state_machine
        self.locale = await LocaleFactory.async_create(options.locale, domain)

        regular_sensors: dict = {
            "powersensormovingaverage": partial(
                HubMember,
                data_type=int,
                listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}",
                initval=0,
            ),
            "power_sensor_moving_average_5": partial(
                Average,
                max_age=300,
                max_samples=300,
                precision=0
            ),
            "powersensormovingaverage24": partial(
                HubMember,
                data_type=int,
                listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION_24H)}",
                initval=0,
            ),
            "power": partial(
                Power,
                configsensor=options.powersensor,
                powersensor_includes_car=options.powersensor_includes_car,
            ),
            "power_trend": partial(
                Gradient,
                max_age=300,
                max_samples=300,
                precision=0
            )
        }
        charger_sensors = {
            "charger_done": partial(
                HubMember,
                data_type=bool,
                listenerentity=f"binary_sensor.{domain}_{nametoid(CHARGER_DONE)}",
                initval=False,
            ),
            "carpowersensor": partial(
                CarPowerSensor,
                data_type=int,
                listenerentity=self.chargertype.entities.powermeter,
                powermeter_factor=self.chargertype.options.powermeter_factor,
                hubdata=self,
                init_override=len(self.chargertype.entities.chargerentity) > 0,
            ),
        }
        resultdict = {}  # needed?
        sensors: dict = {
            "charger_enabled": partial(
                HubMember,
                data_type=bool,
                listenerentity=f"switch.{domain}_{nametoid(CHARGERENABLED)}",
                initval=False,
            ),
            "current_peak": partial(
                CurrentPeak, data_type=float, initval=0, startpeaks=options.startpeaks, options_use_history=options.use_peak_history
            ),
            "totalhourlyenergy": partial(
                HubMember,
                data_type=float,
                listenerentity=f"sensor.{domain}_{nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
                initval=0,
            ),
        }

        if self.chargertype.type is not ChargerType.NoCharger:
            chobj = await self.async_set_chargerobject_and_switch()
            self.chargerobject = chobj[0]
            self.chargerobject_switch = chobj[1]
            self.amp_meter = chobj[2]
            resultdict[self.chargerobject.entity] = (
                chobj[3] or self.chargerobject.is_initialized
            )
            sensors.update(charger_sensors)

        if not options.peaqev_lite:
            sensors.update(regular_sensors)
        for k, v in sensors.items():
            setattr(self, k, v())
        self.sensors_list = [
            self.chargerobject,
            self.chargerobject_switch,
            self.charger_enabled,
            self.charger_done,
        ]
        if self.chargertype.type is not ChargerType.NoCharger:
            self.sensors_list.append(self.amp_meter)

    async def async_set_chargerobject_and_switch(
        self,
    ) -> Tuple[
        ChargerObject, ChargerSwitch, HubMember, bool | None
    ]:  # todo: refactor setup
        regular = {
            "chargerobject": partial(
                ChargerObject,
                data_type=self.chargertype.native_chargerstates,
                listenerentity=self.chargertype.entities.chargerentity,
            ),
            "chargerobject_switch": partial(
                ChargerSwitch,
                hass=self.state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                hubdata=self,
                init_override=True,
            ),
            "amp_meter": partial(
                HubMember,
                data_type=int,
                listenerentity=self.chargertype.entities.ampmeter,
                initval=0,
                hass=self.state_machine,
            ),
        }
        lite = {
            "chargerobject": partial(
                ChargerObject,
                data_type=self.chargertype.native_chargerstates,
                listenerentity="no entity",
                init_override=True,
            ),
            "chargerobject_switch": partial(
                ChargerSwitch,
                hass=self.state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                # currentname=self.chargertype.entities.ampmeter,
                hubdata=self,
            ),
        }
        if len(self.chargertype.entities.chargerentity):
            return (
                regular["chargerobject"](),
                regular["chargerobject_switch"](),
                regular["amp_meter"](),
                None,
            )
        else:
            return (
                lite["chargerobject"](),
                lite["chargerobject_switch"](),
                regular["amp_meter"](),
                True,
            )

    async def async_init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        if self.chargertype.type.value != "None":
            if self.chargerobject is not None:
                self.chargerobject.value = (
                    self.state_machine.states.get(self.chargerobject.entity).state
                    if self.state_machine.states.get(self.chargerobject.entity)
                    is not None
                    else 0
                )
            self.chargerobject_switch.value = (
                self.state_machine.states.get(self.chargerobject_switch.entity).state
                if self.state_machine.states.get(self.chargerobject_switch.entity)
                is not None
                else ""
            )
            self.amp_meter.update()
            self.carpowersensor.value = (
                self.state_machine.states.get(self.carpowersensor.entity).state
                if isinstance(
                    self.state_machine.states.get(self.carpowersensor.entity),
                    (float, int),
                )
                else 0
            )
        self.totalhourlyenergy.value = (
            self.state_machine.states.get(self.totalhourlyenergy.entity)
            if isinstance(
                self.state_machine.states.get(self.totalhourlyenergy.entity),
                (float, int),
            )
            else 0
        )

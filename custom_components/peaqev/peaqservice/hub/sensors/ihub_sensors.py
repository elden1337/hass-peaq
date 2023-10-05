from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Tuple, TYPE_CHECKING

from peaqevcore.common.trend import Gradient
from peaqevcore.models.hub.carpowersensor import CarPowerSensor
from peaqevcore.models.hub.chargerobject import ChargerObject
from peaqevcore.models.hub.chargerswitch import ChargerSwitch
from peaqevcore.models.hub.currentpeak import CurrentPeak
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power
from peaqevcore.services.locale.Locale import LocaleData, LocaleFactory

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.sensors.models.average import Average

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType
from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H, CHARGER_DONE, CHARGERENABLED,
    CONSUMPTION_TOTAL_NAME, HOURLY)
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


@dataclass
class HubSensorsBase:
    state_machine: any = field(init=False)
    locale: LocaleData = field(init=False)
    chargertype: any = field(init=False)
    charger_enabled: HubMember = field(init=False)
    current_peak: CurrentPeak = field(init=False)
    totalhourlyenergy: HubMember = field(init=False)

    async def async_setup(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        self.chargertype: IChargerType = chargerobject
        self.state_machine = state_machine
        self.locale = await LocaleFactory.async_create(options.locale, domain)

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
            ),  #not lite?
        }

        for k, v in sensors.items():
            setattr(self, k, v())

@dataclass
class HubSensors(HubSensorsBase):
    charger_done: HubMember = field(init=False)
    carpowersensor: CarPowerSensor = field(init=False)
    chargerobject: ChargerObject = field(init=False)
    chargerobject_switch: ChargerSwitch = field(init=False)
    amp_meter: HubMember = field(init=False)
    powersensormovingaverage: HubMember = field(init=False)
    powersensormovingaverage24: HubMember = field(init=False)
    power_sensor_moving_average_5: Average = field(init=False)
    power: Power = field(init=False)
    power_trend: Gradient = field(init=False)

    async def async_setup(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        await super().async_setup(options, state_machine, domain, chargerobject)

        regular_sensors: dict = {
            "powersensormovingaverage": partial(
                HubMember,
                data_type=int,
                listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}",
                initval=0,
            ), #not lite
            "power_sensor_moving_average_5": partial(
                Average,
                max_age=300,
                max_samples=300,
                precision=0
            ), #not lite
            "powersensormovingaverage24": partial(
                HubMember,
                data_type=int,
                listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION_24H)}",
                initval=0,
            ), #not lite
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
            ) #not lite
        }
        charger_sensors = {
            "charger_done": partial(
                HubMember,
                data_type=bool,
                listenerentity=f"binary_sensor.{domain}_{nametoid(CHARGER_DONE)}",
                initval=False,
            ),  #not nocharger
            "carpowersensor": partial(
                CarPowerSensor,
                data_type=int,
                listenerentity=self.chargertype.entities.powermeter,
                powermeter_factor=self.chargertype.options.powermeter_factor,
                hubdata=self,
                init_override=len(self.chargertype.entities.chargerentity) > 0,
            ),  #not nocharger
        }
        sensors:dict = {}

        if self.chargertype.type is not ChargerType.NoCharger:
            chobj = await self.async_set_chargerobject_and_switch()
            self.chargerobject = chobj[0]
            self.chargerobject_switch = chobj[1]
            self.amp_meter = chobj[2]
            sensors.update(charger_sensors)

        if not options.peaqev_lite:
            sensors.update(regular_sensors)
        for k, v in sensors.items():
            setattr(self, k, v())
        # self.sensors_list = [
        #     self.chargerobject,
        #     self.chargerobject_switch,
        #     self.charger_enabled,
        #     self.charger_done,
        # ]
        # if self.chargertype.type is not ChargerType.NoCharger:
        #     self.sensors_list.append(self.amp_meter)

    async def async_set_chargerobject_and_switch(
        self,
    ) -> Tuple[
        ChargerObject, ChargerSwitch, HubMember
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
            )
        else:
            return (
                lite["chargerobject"](),
                lite["chargerobject_switch"](),
                regular["amp_meter"](),
            )

    async def async_init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        if self.chargertype.type != ChargerType.NoCharger:
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

# @dataclass
# class HubSensors:
#     sensors_list: list[HubMember] = field(init=False)
#     charger_enabled: HubMember = field(init=False)
#     charger_done: HubMember = field(init=False)
#     current_peak: CurrentPeak = field(init=False)
#     totalhourlyenergy: HubMember = field(init=False)
#     carpowersensor: CarPowerSensor = field(init=False)
#     locale: LocaleData = field(init=False)
#     chargerobject: ChargerObject = field(init=False)
#     chargerobject_switch: ChargerSwitch = field(init=False)
#     amp_meter: HubMember = field(init=False)
#     state_machine: any = field(init=False)
#     powersensormovingaverage: HubMember = field(init=False)
#     powersensormovingaverage24: HubMember = field(init=False)
#     power_sensor_moving_average_5: Average = field(init=False)
#     power: Power = field(init=False)
#     power_trend: Gradient = field(init=False)
#     chargertype: any = field(init=False)
#
#     async def async_setup(
#         self, options: HubOptions, state_machine, domain: str, chargerobject
#     ):
#         self.chargertype: IChargerType = chargerobject
#         self.state_machine = state_machine
#         self.locale = await LocaleFactory.async_create(options.locale, domain)
#
#         regular_sensors: dict = {
#             "powersensormovingaverage": partial(
#                 HubMember,
#                 data_type=int,
#                 listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}",
#                 initval=0,
#             ),
#             "power_sensor_moving_average_5": partial(
#                 Average,
#                 max_age=300,
#                 max_samples=300,
#                 precision=0
#             ),
#             "powersensormovingaverage24": partial(
#                 HubMember,
#                 data_type=int,
#                 listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION_24H)}",
#                 initval=0,
#             ),
#             "power": partial(
#                 Power,
#                 configsensor=options.powersensor,
#                 powersensor_includes_car=options.powersensor_includes_car,
#             ),
#             "power_trend": partial(
#                 Gradient,
#                 max_age=300,
#                 max_samples=300,
#                 precision=0
#             )
#         }
#         charger_sensors = {
#             "charger_done": partial(
#                 HubMember,
#                 data_type=bool,
#                 listenerentity=f"binary_sensor.{domain}_{nametoid(CHARGER_DONE)}",
#                 initval=False,
#             ),
#             "carpowersensor": partial(
#                 CarPowerSensor,
#                 data_type=int,
#                 listenerentity=self.chargertype.entities.powermeter,
#                 powermeter_factor=self.chargertype.options.powermeter_factor,
#                 hubdata=self,
#                 init_override=len(self.chargertype.entities.chargerentity) > 0,
#             ),
#         }
#         resultdict = {}  # needed?
#         sensors: dict = {
#             "charger_enabled": partial(
#                 HubMember,
#                 data_type=bool,
#                 listenerentity=f"switch.{domain}_{nametoid(CHARGERENABLED)}",
#                 initval=False,
#             ),
#             "current_peak": partial(
#                 CurrentPeak, data_type=float, initval=0, startpeaks=options.startpeaks, options_use_history=options.use_peak_history
#             ),
#             "totalhourlyenergy": partial(
#                 HubMember,
#                 data_type=float,
#                 listenerentity=f"sensor.{domain}_{nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
#                 initval=0,
#             ),
#         }
#
#         if self.chargertype.type is not ChargerType.NoCharger:
#             chobj = await self.async_set_chargerobject_and_switch()
#             self.chargerobject = chobj[0]
#             self.chargerobject_switch = chobj[1]
#             self.amp_meter = chobj[2]
#             resultdict[self.chargerobject.entity] = (
#                 chobj[3] or self.chargerobject.is_initialized
#             )
#             sensors.update(charger_sensors)
#
#         if not options.peaqev_lite:
#             sensors.update(regular_sensors)
#         for k, v in sensors.items():
#             setattr(self, k, v())
#         self.sensors_list = [
#             self.chargerobject,
#             self.chargerobject_switch,
#             self.charger_enabled,
#             self.charger_done,
#         ]
#         if self.chargertype.type is not ChargerType.NoCharger:
#             self.sensors_list.append(self.amp_meter)
#
#     async def async_set_chargerobject_and_switch(
#         self,
#     ) -> Tuple[
#         ChargerObject, ChargerSwitch, HubMember, bool | None
#     ]:  # todo: refactor setup
#         regular = {
#             "chargerobject": partial(
#                 ChargerObject,
#                 data_type=self.chargertype.native_chargerstates,
#                 listenerentity=self.chargertype.entities.chargerentity,
#             ),
#             "chargerobject_switch": partial(
#                 ChargerSwitch,
#                 hass=self.state_machine,
#                 data_type=bool,
#                 listenerentity=self.chargertype.entities.powerswitch,
#                 initval=False,
#                 hubdata=self,
#                 init_override=True,
#             ),
#             "amp_meter": partial(
#                 HubMember,
#                 data_type=int,
#                 listenerentity=self.chargertype.entities.ampmeter,
#                 initval=0,
#                 hass=self.state_machine,
#             ),
#         }
#         lite = {
#             "chargerobject": partial(
#                 ChargerObject,
#                 data_type=self.chargertype.native_chargerstates,
#                 listenerentity="no entity",
#                 init_override=True,
#             ),
#             "chargerobject_switch": partial(
#                 ChargerSwitch,
#                 hass=self.state_machine,
#                 data_type=bool,
#                 listenerentity=self.chargertype.entities.powerswitch,
#                 initval=False,
#                 # currentname=self.chargertype.entities.ampmeter,
#                 hubdata=self,
#             ),
#         }
#         if len(self.chargertype.entities.chargerentity):
#             return (
#                 regular["chargerobject"](),
#                 regular["chargerobject_switch"](),
#                 regular["amp_meter"](),
#                 None,
#             )
#         else:
#             return (
#                 lite["chargerobject"](),
#                 lite["chargerobject_switch"](),
#                 regular["amp_meter"](),
#                 True,
#             )
#
#     async def async_init_hub_values(self):
#         """Initialize values from Home Assistant on the set objects"""
#         if self.chargertype.type != ChargerType.NoCharger:
#             if self.chargerobject is not None:
#                 self.chargerobject.value = (
#                     self.state_machine.states.get(self.chargerobject.entity).state
#                     if self.state_machine.states.get(self.chargerobject.entity)
#                     is not None
#                     else 0
#                 )
#             self.chargerobject_switch.value = (
#                 self.state_machine.states.get(self.chargerobject_switch.entity).state
#                 if self.state_machine.states.get(self.chargerobject_switch.entity)
#                 is not None
#                 else ""
#             )
#             self.amp_meter.update()
#             self.carpowersensor.value = (
#                 self.state_machine.states.get(self.carpowersensor.entity).state
#                 if isinstance(
#                     self.state_machine.states.get(self.carpowersensor.entity),
#                     (float, int),
#                 )
#                 else 0
#             )
#         self.totalhourlyenergy.value = (
#             self.state_machine.states.get(self.totalhourlyenergy.entity)
#             if isinstance(
#                 self.state_machine.states.get(self.totalhourlyenergy.entity),
#                 (float, int),
#             )
#             else 0
#         )
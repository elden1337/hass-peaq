from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Tuple

from peaqevcore.models.hub.carpowersensor import CarPowerSensor
from peaqevcore.models.hub.chargerobject import ChargerObject
from peaqevcore.models.hub.chargerswitch import ChargerSwitch
from peaqevcore.models.hub.currentpeak import CurrentPeak
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power
from peaqevcore.services.locale.Locale import LocaleData, LocaleFactory

from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H, CHARGERDONE, CHARGERENABLED,
    CONSUMPTION_TOTAL_NAME, HOURLY)
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


@dataclass
class HubSensors:
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
    power: Power = field(init=False)
    chargertype: any = field(init=False)

    async def async_setup(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        self.chargertype = chargerobject
        self.state_machine = state_machine
        self.locale = await LocaleFactory.async_create(options.locale, domain)

        regular_sensors: dict = {
            "powersensormovingaverage": partial(
                HubMember,
                data_type=int,
                listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}",
                initval=0,
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
        }
        charger_sensors = {
            "charger_done": partial(
                HubMember,
                data_type=bool,
                listenerentity=f"binary_sensor.{domain}_{nametoid(CHARGERDONE)}",
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
                CurrentPeak, data_type=float, initval=0, startpeaks=options.startpeaks
            ),
            "totalhourlyenergy": partial(
                HubMember,
                data_type=float,
                listenerentity=f"sensor.{domain}_{nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
                initval=0,
            ),
        }

        if self.chargertype.type.value != "None":
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

    async def async_set_chargerobject_and_switch(
        self,
    ) -> Tuple[ChargerObject, ChargerSwitch, HubMember, bool | None]:  # todo: refactor setup
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
                #currentname=self.chargertype.entities.ampmeter,
                hubdata=self,
                init_override=True,
            ),
            "amp_meter": partial(
                HubMember,
                data_type=int,
                listenerentity=self.chargertype.entities.ampmeter,
                initval=0,
                hass=self.state_machine
            )
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
                #currentname=self.chargertype.entities.ampmeter,
                hubdata=self,
            )
        }
        if len(self.chargertype.entities.chargerentity):
            return regular["chargerobject"](), regular["chargerobject_switch"](),regular["amp_meter"](), None
        else:
            return lite["chargerobject"](), lite["chargerobject_switch"](),regular["amp_meter"](), True

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
            await self.amp_meter.async_update()
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

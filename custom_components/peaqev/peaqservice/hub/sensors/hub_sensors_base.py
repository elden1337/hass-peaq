from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import partial
from typing import TYPE_CHECKING, Tuple

from peaqevcore.models.hub.carpowersensor import CarPowerSensor
from peaqevcore.models.hub.chargerobject import ChargerObject
from peaqevcore.models.hub.chargerswitch import ChargerSwitch
from peaqevcore.models.hub.currentpeak import CurrentPeak
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.services.locale.Locale import LocaleData, LocaleFactory

from custom_components.peaqev.peaqservice.hub.sensors.const import *

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.chargertypes.icharger_type import IChargerType

from custom_components.peaqev.peaqservice.hub.const import (
    CHARGER_DONE, CHARGERENABLED, CONSUMPTION_TOTAL_NAME, HOURLY)
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid

_LOGGER = logging.getLogger(__name__)


@dataclass
class HubSensorsBase:
    domain: str = field(init=False)
    state_machine: any = field(init=False)
    locale: LocaleData = field(init=False)
    chargertype: any = field(init=False)
    charger_enabled: HubMember = field(init=False)
    current_peak: CurrentPeak = field(init=False)
    totalhourlyenergy: HubMember = field(init=False)
    charger_done: HubMember = field(init=False)
    carpowersensor: CarPowerSensor = field(init=False)
    chargerobject: ChargerObject = field(init=False)
    chargerobject_switch: ChargerSwitch = field(init=False)
    amp_meter: HubMember = field(init=False)

    async def async_setup_base(
        self, options: HubOptions, state_machine, domain: str, chargerobject
    ):
        self.chargertype: IChargerType = chargerobject
        self.state_machine = state_machine
        self.locale = await LocaleFactory.async_create(options.locale, domain)
        self.domain = domain

        sensors: dict = {
            CHARGERENABLED_SENSOR: partial(
                HubMember,
                data_type=bool,
                listenerentity=f'switch.{domain}_{nametoid(CHARGERENABLED)}',
                initval=False,
            ),
            CURRENTPEAK_SENSOR: partial(
                CurrentPeak, data_type=float, initval=0, startpeaks=options.startpeaks, locale=self.locale, options_use_history=options.use_peak_history
            ),
            TOTALHOURLYENERGY_SENSOR: partial(
                HubMember,
                data_type=float,
                listenerentity=f'sensor.{domain}_{nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}',
                initval=0,
            )
        }

        self._set_sensors(sensors)

    def _set_sensors(self, sensors:dict):
        for k, v in sensors.items():
            setattr(self, k, v())

    async def async_set_charger_sensors(self) -> None:
        """Not for type nocharger"""
        charger_sensors = {
            CHARGERDONE_SENSOR:   partial(
                HubMember,
                data_type=bool,
                listenerentity=f'binary_sensor.{self.domain}_{nametoid(CHARGER_DONE)}',
                initval=False,
            ),
            CARPOWERSENSOR_SENSOR: partial(
                CarPowerSensor,
                data_type=int,
                listenerentity=self.chargertype.entities.powermeter,
                powermeter_factor=self.chargertype.options.powermeter_factor,
                hubdata=self,
                init_override=len(self.chargertype.entities.chargerentity) > 0,
            ),
        }

        chobj = await self.async_set_chargerobject_and_switch()
        self.chargerobject = chobj[0]
        self.chargerobject_switch = chobj[1]
        self.amp_meter = chobj[2]

        self._set_sensors(charger_sensors)

    async def async_set_chargerobject_and_switch(
        self,
    ) -> Tuple[
        ChargerObject, ChargerSwitch, HubMember
    ]:  # todo: refactor setup
        regular = {
            CHARGEROBJECT_SENSOR: partial(
                ChargerObject,
                data_type=self.chargertype.native_chargerstates,
                listenerentity=self.chargertype.entities.chargerentity,
            ),
            CHARGEROBJECT_SWITCH_SENSOR: partial(
                ChargerSwitch,
                hass=self.state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                hubdata=self,
                init_override=True,
            ),
            AMP_METER_SENSOR: partial(
                HubMember,
                data_type=int,
                listenerentity=self.chargertype.entities.ampmeter,
                initval=0,
                hass=self.state_machine,
            ),
        }
        lite = {
            CHARGEROBJECT_SENSOR: partial(
                ChargerObject,
                data_type=self.chargertype.native_chargerstates,
                listenerentity='no entity',
                init_override=True,
            ),
            CHARGEROBJECT_SWITCH_SENSOR: partial(
                ChargerSwitch,
                hass=self.state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                hubdata=self,
            ),
        }
        if len(self.chargertype.entities.chargerentity):
            _LOGGER.debug(f'Initializing Chargerobject with: data_type: {self.chargertype.native_chargerstates}, listenerentity: {self.chargertype.entities.chargerentity}')
            return (
                regular['chargerobject'](),
                regular['chargerobject_switch'](),
                regular['amp_meter'](),
            )
        else:
            return (
                lite['chargerobject'](),
                lite['chargerobject_switch'](),
                regular['amp_meter'](),
            )

    async def async_init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        self.totalhourlyenergy.value = (
            self.state_machine.states.get(self.totalhourlyenergy.entity)
            if isinstance(
                self.state_machine.states.get(self.totalhourlyenergy.entity),
                (float, int),
            )
            else 0
        )

    async def async_init_charger_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
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
            else ''
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

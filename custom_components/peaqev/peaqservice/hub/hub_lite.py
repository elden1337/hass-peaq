import logging
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.hub.hub import Hub
from peaqevcore.hub.hub_options import HubOptions

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite
from custom_components.peaqev.peaqservice.hub.hubbase import HubBase
from custom_components.peaqev.peaqservice.hub.nordpool import NordPoolUpdater
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HubLite(HubBase, Hub):
    """This is the hub used for peaqev-lite. Without power meter readings"""
    def __init__(
        self,
        hass: HomeAssistant,
        options: HubOptions,
        domain: str,
        config_inputs: dict
        ):

        HubBase.__init__(self, hass=hass, options=options, domain=domain)
        Hub.__init__(self, state_machine=hass, options=options, domain=domain, chargerobj=self.chargertype)

        self.chargecontroller = ChargeControllerLite(self)

        trackerEntities = [
            self.sensors.chargerobject_switch.entity,
            self.sensors.totalhourlyenergy.entity
        ]

        self.chargingtracker_entities = [
            self.sensors.carpowersensor.entity,
            self.sensors.charger_enabled.entity,
            self.sensors.charger_done.entity,
            self.sensors.chargerobject.entity,
            f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}",
        ]

        if self.hours.price_aware is True:
            self.nordpool = NordPoolUpdater(hass=self.hass, hub=self)
            if self.hours.nordpool_entity is not None:
                self.chargingtracker_entities.append(self.hours.nordpool_entity)

        trackerEntities += self.chargingtracker_entities

        async_track_state_change(hass, trackerEntities, self.state_changed)

    def is_initialized(self) -> bool:
        ret = [#elf.hours.is_initialized,
               self.sensors.carpowersensor.is_initialized,
               self.sensors.chargerobject_switch.is_initialized,
               self.sensors.chargerobject.is_initialized
               ]
        return all(ret)

    @property
    def current_peak_dynamic(self):
        if self.price_aware is True and len(self.dynamic_caution_hours):
            if datetime.now().hour in self.dynamic_caution_hours.keys() and self.timer.is_override is False:
                return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.sensors.current_peak.value

    @property
    def non_hours(self) -> list:
        return self.scheduler.non_hours if self.scheduler.scheduler_active else self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        return self.scheduler.caution_hours if self.scheduler.scheduler_active else self.hours.dynamic_caution_hours

    async def _update_sensor(self, entity, value):
        match entity:
            case self.sensors.carpowersensor.entity:
                self.sensors.carpowersensor.value = value
                self.sensors.chargerobject_switch.updatecurrent()
            case self.sensors.chargerobject.entity:
                self.sensors.chargerobject.value = value
            case self.sensors.chargerobject_switch.entity:
                self.sensors.chargerobject_switch.value = value
                self.sensors.chargerobject_switch.updatecurrent()
            case self.sensors.current_peak.entity:
                self.sensors.current_peak.value = value
            case self.sensors.totalhourlyenergy.entity:
                self.sensors.totalhourlyenergy.value = value
                self.sensors.current_peak.value = self.sensors.locale.data.query_model.observed_peak
                self.sensors.locale.data.query_model.try_update(
                    new_val=float(value),
                    timestamp=datetime.now()
                )
            case self.nordpool.nordpool_entity:
                self.nordpool.update_nordpool()

        if entity in self.chargingtracker_entities:
            await self.charger.charge()

    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.sensors.charger_enabled.value = True
        self.sensors.charger_done.value = False

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.sensors.charger_enabled.value = False
        self.sensors.charger_done.value = False

    async def call_override_nonhours(self, hours:int=1):
        """peaqev.override_nonhours"""
        self.timer.update(hours)

    async def call_schedule_needed_charge(
            self,
            charge_amount:float,
            departure_time:str,
            schedule_starttime:str = None,
            override_settings:bool = False
        ):
        dep_time = datetime.strptime(departure_time, '%y-%m-%d %H:%M')
        if schedule_starttime is not None:
            start_time = datetime.strptime(schedule_starttime, '%y-%m-%d %H:%M')
        else:
            start_time = datetime.now()
        _LOGGER.debug(f"scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}")
        self.scheduler.create_schedule(charge_amount, dep_time, start_time, override_settings)
        self.scheduler.update()

    async def call_scheduler_cancel(self):
        self.scheduler.cancel()
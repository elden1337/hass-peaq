import logging
import time
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
    callback
)
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.hub.hub import Hub
from peaqevcore.hub.hub_options import HubOptions

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite
from custom_components.peaqev.peaqservice.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData
from custom_components.peaqev.peaqservice.hub.nordpool import NordPoolUpdater
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.state_changes import StateChanges
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER, SMARTOUTLET

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub(Hub):
    hub_id = 1337
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0

    def __init__(
        self,
        hass: HomeAssistant,
        options: HubOptions,
        domain: str,
        config_inputs: dict
        ):

        self.hubname = domain.capitalize()
        self.chargertype = ChargerTypeData(
            hass=hass,
            input_type=options.charger.chargertype,
            options=options
        )
        self.charger = Charger(
            self,
            hass,
            self.chargertype.charger.servicecalls
        )

        Hub.__init__(
            self,
            state_machine=hass,
            options=options,
            domain=domain,
            chargerobj=self.chargertype
        )

        self.servicecalls = ServiceCalls(self)
        self.states = StateChanges(self)

        trackerEntities = [
            self.sensors.totalhourlyenergy.entity
        ]

        if options.peaqev_lite:
            self.chargecontroller = ChargeControllerLite(self)
        else:
            self.configpower_entity = config_inputs["powersensor"]
            self.chargecontroller = ChargeController(self) #move to core
            trackerEntities.append(self.configpower_entity)

        if self.hours.price_aware is True:
            self.nordpool = NordPoolUpdater(hass=self.state_machine, hub=self)

        self.chargingtracker_entities = self._set_chargingtracker_entities()
        trackerEntities += self.chargingtracker_entities
        async_track_state_change(hass, trackerEntities, self.state_changed)

    @property
    def non_hours(self) -> list:
        if self.scheduler.scheduler_active:
            return self.scheduler.non_hours
        return self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        if self.scheduler.scheduler_active:
            return self.scheduler.caution_hours
        return self.hours.dynamic_caution_hours

    @property
    def current_peak_dynamic(self):
        if self.options.price.price_aware is True and len(self.dynamic_caution_hours) > 0:
            if datetime.now().hour in self.dynamic_caution_hours.keys() and self.timer.is_override is False:
                return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.sensors.current_peak.value

    @property
    def is_initialized(self) -> bool:
        ret = {"hours": self.hours.is_initialized,
               "carpowersensor": self.sensors.carpowersensor.is_initialized,
               "chargerobject_switch": self.sensors.chargerobject_switch.is_initialized,
               "power": self.sensors.power.is_initialized,
               "chargerobject": self.sensors.chargerobject.is_initialized
               }
        if all(ret.values()):
            return True
        not_ready = []
        for r in ret:
            if ret[r] is False:
                not_ready.append(r)
        if len(not_ready) != self.not_ready_list_old_state or self.initialized_log_last_logged - time.time() > 30:
            _LOGGER.warning(f"{not_ready} has not initialized yet.")
            self.not_ready_list_old_state = len(not_ready)
            self.initialized_log_last_logged = time.time()
        if "chargerobject" in not_ready:
            self.chargertype.charger.getentities()
        return False

    def _set_chargingtracker_entities(self) -> list:
        ret = [
            self.sensors.chargerobject_switch.entity,
            self.sensors.carpowersensor.entity,
            self.sensors.charger_enabled.entity,
            self.sensors.charger_done.entity,
            f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}",
        ]

        if self.chargertype.charger.domainname != SMARTOUTLET:
            ret.append(self.sensors.chargerobject.entity)
        if self.options.peaqev_lite is False:
            ret.append(self.sensors.powersensormovingaverage.entity)
            ret.append(self.sensors.powersensormovingaverage24.entity)
        if self.hours.nordpool_entity is not None:
            ret.append(self.hours.nordpool_entity)
        return ret

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        if entity_id is not None:
            try:
                if old_state is None or old_state != new_state:
                    await self.states.update_sensor(entity_id, new_state.state)
            except Exception as e:
                msg = f"Unable to handle data: {entity_id} ({e}) {old_state}|{new_state}"
                _LOGGER.error(msg)

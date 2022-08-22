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
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub(Hub):
    """This is the hub used under normal circumstances. Ie when there is a power-meter to read from."""
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
            hass,
            options.chargertype,
            options.chargerid
        )
        self.charger = Charger(
            self,
            hass,
            self.chargertype.charger.servicecalls
        )

        Hub.__init__(self, state_machine=hass, options=options, domain=domain, chargerobj=self.chargertype)

        self.servicecalls = ServiceCalls(self)

        if options.peaqev_lite:
            self.chargecontroller = ChargeControllerLite(self)
        else:
            self.configpower_entity = config_inputs["powersensor"]
            self.chargecontroller = ChargeController(self) #move to core

        trackerEntities = [
            self.sensors.totalhourlyenergy.entity
        ]

        self.chargingtracker_entities = [
            self.sensors.chargerobject_switch.entity,
            self.sensors.carpowersensor.entity,
            self.sensors.charger_enabled.entity,
            self.sensors.charger_done.entity,
            self.sensors.chargerobject.entity,
            f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}",
            ]

        if options.peaqev_lite is False:
            trackerEntities.append(self.configpower_entity)
            self.chargingtracker_entities.append(self.sensors.powersensormovingaverage.entity)
            self.chargingtracker_entities.append(self.sensors.powersensormovingaverage24.entity)

        if self.hours.price_aware is True:
            self.nordpool = NordPoolUpdater(hass=self.state_machine, hub=self)
            if self.hours.nordpool_entity is not None:
                self.chargingtracker_entities.append(self.hours.nordpool_entity)

        trackerEntities += self.chargingtracker_entities
        async_track_state_change(hass, trackerEntities, self.state_changed)

    @property
    def non_hours(self) -> list:
        return self.scheduler.non_hours if self.scheduler.scheduler_active else self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        return self.scheduler.caution_hours if self.scheduler.scheduler_active else self.hours.dynamic_caution_hours

    @property
    def current_peak_dynamic(self):
        if self.options.price.price_aware is True and len(self.dynamic_caution_hours):
            if datetime.now().hour in self.dynamic_caution_hours.keys() and self.timer.is_override is False:
                return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.sensors.current_peak.value

    @property
    def is_initialized(self) -> bool:
        ret = {#"hours": self.hours.is_initialized,
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

    async def _update_sensor(self, entity, value):
        update_session = False
        if self.options.peaqev_lite is True:
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
        else:
            match entity:
                case self.configpower_entity:
                    self.sensors.power.update(
                        carpowersensor_value=self.sensors.carpowersensor.value,
                        config_sensor_value=value
                    )
                    update_session = True
                case self.sensors.carpowersensor.entity:
                    self.sensors.carpowersensor.value = value
                    self.sensors.power.update(
                        carpowersensor_value=self.sensors.carpowersensor.value,
                        config_sensor_value=None
                    )
                    update_session = True
                    self.sensors.chargerobject_switch.updatecurrent()
                case self.sensors.chargerobject.entity:
                    self.sensors.chargerobject.value = value
                case self.sensors.chargerobject_switch.entity:
                    self.sensors.chargerobject_switch.value = value
                    self.sensors.chargerobject_switch.updatecurrent()
                case self.sensors.totalhourlyenergy.entity:
                    self.sensors.totalhourlyenergy.value = value
                    self.sensors.current_peak.value = self.sensors.locale.data.query_model.observed_peak
                    self.sensors.locale.data.query_model.try_update(
                        new_val=float(value),
                        timestamp=datetime.now()
                    )
                case self.sensors.powersensormovingaverage.entity:
                    self.sensors.powersensormovingaverage.value = value
                case self.sensors.powersensormovingaverage24.entity:
                    self.sensors.powersensormovingaverage24.value = value
                case self.nordpool.nordpool_entity:
                    self.nordpool.update_nordpool()
                    update_session = True

        if self.charger.session_is_active and update_session:
            self.charger.session.session_energy = self.sensors.carpowersensor.value
            self.charger.session.session_price = float(self.nordpool.state)
        if self.scheduler.schedule_created is True:
            self.scheduler.update()
        if entity in self.chargingtracker_entities and self.is_initialized is True:
            await self.charger.charge()

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._update_sensor(entity_id, new_state.state)
        except Exception as e:
            msg = f"Unable to handle data: {entity_id} ({e})"
            _LOGGER.error(msg)

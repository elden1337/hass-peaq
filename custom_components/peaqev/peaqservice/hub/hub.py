from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
    callback
)
from homeassistant.helpers.event import async_track_state_change
from peaqevcore.hub.hub_options import HubOptions
from peaqevcore.hub.hub_sensors import HubSensorsFactory
from peaqevcore.services.hourselection.initializers.hoursbase import Hours
from peaqevcore.services.hourselection.initializers.hourselectionfactory import HourselectionFactory
from peaqevcore.services.prediction.prediction import Prediction
from peaqevcore.services.scheduler.scheduler import SchedulerFacade
from peaqevcore.services.threshold.thresholdfactory import ThresholdFactory
from peaqevcore.services.timer.timer import Timer

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_factory import ChargeControllerFactory
from custom_components.peaqev.peaqservice.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargertypes.chargertype_factory import ChargerTypeFactory
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.hub.hub_initializer import HubInitializer
from custom_components.peaqev.peaqservice.hub.nordpool.nordpool import NordPoolUpdater
from custom_components.peaqev.peaqservice.hub.observer import Observer
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes_factory import StateChangesFactory
from custom_components.peaqev.peaqservice.hub.svk import svk
from custom_components.peaqev.peaqservice.power_canary.power_canary import PowerCanary
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)


class HomeAssistantHub:
    hub_id = 1337

    def __init__(
            self,
            hass: HomeAssistant,
            options: HubOptions,
            domain: str
    ):
        self.state_machine = hass
        self.domain = domain
        self.options: HubOptions = options
        self._is_initialized = False
        self.observer = Observer(self)
        self.hubname = domain.capitalize()
        self.chargertype = ChargerTypeFactory.create(hass=hass, input_type=self.options.charger.chargertype,
                                                     options=self.options)
        self.charger = Charger(hub=self, hass=hass, servicecalls=self.chargertype.servicecalls)
        self.sensors = HubSensorsFactory.create(self.options)
        self.timer: Timer = Timer()
        self.hours: Hours = HourselectionFactory.create(self)
        self.threshold = ThresholdFactory.create(self)
        self.prediction = Prediction(self)
        self.scheduler = SchedulerFacade(hub=self, options=self.hours.options)

        self.sensors.setup(state_machine=hass, options=options, domain=domain, chargerobject=self.chargertype)
        self.sensors.init_hub_values()

        self.servicecalls = ServiceCalls(self)
        self.states = StateChangesFactory.create(self)
        self.svk = svk(self)  # interim solution for svk peak hours
        self.chargecontroller = ChargeControllerFactory.create(self, chargerstates=self.chargertype.chargerstates)
        self.nordpool = NordPoolUpdater(hass=hass, hub=self, is_active=self.hours.price_aware)
        self.power_canary = PowerCanary(hub=self)
        self.initializer = HubInitializer(self)

        tracker_entities = []

        if not options.peaqev_lite:
            tracker_entities.append(self.options.powersensor)
            tracker_entities.append(self.sensors.totalhourlyenergy.entity)

        self.chargingtracker_entities = self._set_chargingtracker_entities()
        tracker_entities += self.chargingtracker_entities
        async_track_state_change(hass, tracker_entities, self.state_changed)

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
        """Dynamically calculated peak to adhere to caution-hours"""
        if self.options.price.price_aware and len(self.dynamic_caution_hours) > 0:
            if datetime.now().hour in self.dynamic_caution_hours.keys() and not self.timer.is_override:
                return self.sensors.current_peak.value * self.dynamic_caution_hours[datetime.now().hour]
        return self.sensors.current_peak.value

    @property
    def is_initialized(self) -> bool:
        if hasattr(self, "initializer"):
            if self.initializer.check():
                del self.initializer
                return True
            return False
        return True

    def _set_chargingtracker_entities(self) -> list:
        ret = [f"sensor.{self.domain}_{ex.nametoid(CHARGERCONTROLLER)}"]
        if hasattr(self.sensors, "chargerobject_switch"):
            ret.append(self.sensors.chargerobject_switch.entity)
        if hasattr(self.sensors, "carpowersensor"):
            ret.append(self.sensors.carpowersensor.entity)
        if hasattr(self.sensors, "charger_enabled"):
            ret.append(self.sensors.charger_enabled.entity)
        if hasattr(self.sensors, "charger_done"):
            ret.append(self.sensors.charger_done.entity)

        if self.chargertype.type not in [ChargerType.Outlet, ChargerType.NoCharger]:
            ret.append(self.sensors.chargerobject.entity)
        if not self.options.peaqev_lite:
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
                msg = f"Unable to handle data-update: {entity_id} {old_state}|{new_state}. Exception: {e}"
                _LOGGER.error(msg)

    """Composition below here"""

    def get_chargerobject(self) -> str:
        ret = getattr(self.sensors.chargerobject, "value", "unknown")
        return ret.lower()


from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub import HomeAssistantHub

import logging
import time
from enum import Enum

from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import \
    HourselectionFactory

_LOGGER = logging.getLogger(__name__)


class InitializerTypes(Enum):
    Hours = "Hours"
    CarPowerSensor = "Car powersensor"
    ChargerObjectSwitch = "Chargerobject switch"
    Power = "Power"
    ChargerObject = "Chargerobject"
    ChargerType = "Chargertype"


class HubInitializer:
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0

    def __init__(self, hub: HomeAssistantHub):
        self.parent:HomeAssistantHub = hub
        self._initialized: bool = False

    def check(self):
        if self._initialized:
            return True
        else:
            return self._check

    def _check(self) -> bool:
        init_types = {InitializerTypes.Hours: self.parent.hours.is_initialized}
        if hasattr(self.parent.sensors, "carpowersensor"):
            init_types[InitializerTypes.CarPowerSensor] = self.parent.sensors.carpowersensor.is_initialized
        if hasattr(self.parent.sensors, "chargerobject_switch"):
            init_types[
                InitializerTypes.ChargerObjectSwitch
            ] = self.parent.sensors.chargerobject_switch.is_initialized
        if hasattr(self.parent.sensors, "power"):
            init_types[InitializerTypes.Power] = self.parent.sensors.power.is_initialized
        if hasattr(self.parent.sensors, "chargerobject"):
            init_types[InitializerTypes.ChargerObject] = self.parent.sensors.chargerobject.is_initialized
        init_types[InitializerTypes.ChargerType] = self.parent.chargertype.is_initialized
        if all(init_types.values()):
            self._initialized = True
            _LOGGER.info("Hub is ready to use.")
            _LOGGER.debug(
                f"Hub is initialized with {self.parent.options.price.cautionhour_type} as cautionhourtype."
            )
            return True
        return self.scramble_not_initialized(init_types)

    def scramble_not_initialized(self, init_types) -> bool:
        not_ready = [r.value for r in init_types if init_types[r] is False]
        if any(
            [
                len(not_ready) != self.not_ready_list_old_state,
                self.initialized_log_last_logged - time.time() > 30,
            ]
        ):
            _LOGGER.info(f"Hub is awaiting {not_ready} before being ready to use.")
            self.not_ready_list_old_state = len(not_ready)
            self.initialized_log_last_logged = time.time()
        if [InitializerTypes.ChargerObject, InitializerTypes.ChargerType] in not_ready:
            if self.parent.chargertype.async_setup():
                self.parent.chargertype.is_initialized = True
        return False


    async def async_init_hours(self):
        self.parent.hours = await HourselectionFactory.async_create(self.parent)
        if self.parent.options.price.price_aware:
            await self.parent.hours.async_update_prices(
                self.parent.nordpool.model.prices,
                self.parent.nordpool.model.prices_tomorrow)
        _LOGGER.debug("Re-initializing Hoursclasses.")
from __future__ import annotations

import logging
import time

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import \
    HourselectionFactory
from custom_components.peaqev.peaqservice.hub.models.initializer_types import \
    InitializerTypes
from custom_components.peaqev.peaqservice.util.constants import \
    CHARGERCONTROLLER
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid

_LOGGER = logging.getLogger(__name__)


class HubInitializerMixin:
    """Mixin class to Hub that handles initialization of the hub."""
    initialized_log_last_logged = 0
    not_ready_list_old_state = 0
    _initialized: bool = False

    def check_initializer(self):
        if self._initialized:
            return True
        else:
            return self._check

    def _check(self) -> bool:
        init_types = {InitializerTypes.Hours: self.hours.is_initialized}
        if self.options.price.price_aware:
            init_types[InitializerTypes.SpotPrice] = self.spotprice.is_initialized
        if hasattr(self.sensors, "carpowersensor"):
            init_types[InitializerTypes.CarPowerSensor] = self.sensors.carpowersensor.is_initialized
        if hasattr(self.sensors, "chargerobject_switch"):
            init_types[
                InitializerTypes.ChargerObjectSwitch
            ] = self.sensors.chargerobject_switch.is_initialized
        if hasattr(self.sensors, "power"):
            init_types[InitializerTypes.Power] = self.sensors.power.is_initialized
        if hasattr(self.sensors, "chargerobject"):
            init_types[InitializerTypes.ChargerObject] = self.sensors.chargerobject.is_initialized
        init_types[InitializerTypes.ChargerType] = self.chargertype.is_initialized
        if all(init_types.values()):
            self._initialized = True
            _LOGGER.info("Hub is ready to use.")
            _LOGGER.debug(
                f"Hub is initialized with {self.options.price.cautionhour_type} as cautionhourtype."
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
            if self.chargertype.async_setup():
                self.chargertype.is_initialized = True
        return False


    async def async_init_hours(self):
        self.hours = await HourselectionFactory.async_create(self)
        if self.options.price.price_aware:
            await self.hours.async_update_prices(
                self.spotprice.model.prices,
                self.spotprice.model.prices_tomorrow)
        _LOGGER.debug("Re-initializing Hoursclasses.")

    async def async_setup_tracking(self) -> list:
        tracker_entities = []
        if not self.options.peaqev_lite:
            tracker_entities.append(self.options.powersensor)
            tracker_entities.append(self.sensors.totalhourlyenergy.entity)
        self.chargingtracker_entities = await self.async_set_chargingtracker_entities()
        tracker_entities += self.chargingtracker_entities
        return tracker_entities

    async def async_set_chargingtracker_entities(self) -> list:
        ret = [f"sensor.{self.domain}_{nametoid(CHARGERCONTROLLER)}"]
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
        if self.options.price.price_aware:
            ret.append(getattr(self.spotprice, "entity", ""))
        return ret

    def _set_observers(self) -> None:
        self.observer.add("prices changed", self.async_update_prices)
        self.observer.add(
            "adjusted average price changed", self.async_update_adjusted_average
        )
        self.observer.add("update charger done", self.async_update_charger_done)
        self.observer.add("update charger enabled", self.async_update_charger_enabled)
        self.observer.add(
            "dynamic max price changed", self.async_update_average_monthly_price
        )
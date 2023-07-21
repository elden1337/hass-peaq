from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging
import time
from abc import abstractmethod
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class IStateChanges:
    latest_nordpool_update = 0
    latest_outlet_update = 0
    latest_chargecontroller_update = 0

    def __init__(self, hub: HomeAssistantHub):
        self.hub = hub

    async def async_update_sensor(self, entity, value):
        update_session = await self.async_update_sensor_internal(entity, value)
        if time.time() - self.latest_chargecontroller_update > 3:
            self.latest_chargecontroller_update = time.time()
            await self.hub.chargecontroller.async_set_status()
            if self.hub.options.price.price_aware:  # todo: strategy should handle this
                if not self.hub.max_min_controller.override_max_charge:
                    await self.hub.max_min_controller.async_reset_max_charge_sensor()
        if self.hub.options.price.price_aware:  # todo: strategy should handle this
            if entity != self.hub.nordpool.nordpool_entity and (
                not self.hub.hours.is_initialized
                or time.time() - self.latest_nordpool_update > 60
            ):
                """tweak to provoke nordpool to update more often"""
                self.latest_nordpool_update = time.time()
                await self.hub.nordpool.async_update_nordpool()
        await self.async_handle_sensor_attribute()
        await self.async_update_session_parameters(update_session)
        if all(
            [
                entity in self.hub.chargingtracker_entities,
                self.hub.is_initialized,
                self.hub.chargertype is not ChargerType.NoCharger,  # todo: strategy should handle this
            ]
        ):
            await self.hub.chargecontroller.charger.async_charge()

    async def async_update_session_parameters(self, update_session: bool) -> None:
        if all(
            [
                self.hub.chargecontroller.charger.session_active,
                update_session,
                hasattr(self.hub.sensors, "carpowersensor"),
            ]
        ):
            await self.hub.chargecontroller.session.async_set_session_energy(
                getattr(self.hub.sensors.carpowersensor, "value")
            )
            if self.hub.options.price.price_aware:  # todo: strategy should handle this
                await self.hub.chargecontroller.session.async_set_session_price(
                    float(self.hub.nordpool.state)
                )
                if getattr(self.hub.hours.scheduler, "schedule_created", False):
                    await self.hub.hours.scheduler.async_update_facade()

    async def async_handle_sensor_attribute(self) -> None:
        # is this needed if we loop them all?
        if hasattr(self.hub.sensors, "carpowersensor"):
            if self.hub.sensors.carpowersensor.use_attribute:  # todo: strategy should handle this
                entity = self.hub.sensors.carpowersensor
                try:
                    val = self.hub.state_machine.states.get(
                        entity.entity
                    ).attributes.get(entity.attribute)
                    if val is not None:
                        self.hub.sensors.carpowersensor.value = val
                        await self.hub.sensors.power.async_update(
                            carpowersensor_value=self.hub.sensors.carpowersensor.value,
                            config_sensor_value=None,
                        )
                    return
                except Exception as e:
                    _LOGGER.debug(
                        f"Unable to get attribute-state for {entity.entity}|{entity.attribute}. {e}"
                    )

    async def async_update_chargerobject_switch(self, value) -> None:
        self.hub.sensors.chargerobject_switch.value = value
        await self.async_handle_outlet_updates()

    async def async_update_total_energy_and_peak(self, value) -> None:
        try:
            self.hub.sensors.totalhourlyenergy.value = value
        except:
            _LOGGER.debug(f"Unable to set totalhourlyenergy to {value}")

        try:
            await self.hub.sensors.locale.async_try_update_peak(
                new_val=float(value), timestamp=datetime.now()
            )
        except:
            _LOGGER.debug(f"Unable to update peak to {value}")
        try:
            self.hub.sensors.current_peak.value = (
                self.hub.sensors.locale.data.query_model.observed_peak
            )
        except:
            _LOGGER.debug(f"Unable to set current_peak to {value}")

        try:
            await self.hub.chargecontroller.savings.async_add_consumption(float(value))
        except:
            _LOGGER.debug(f"Unable to add consumption to savings")
        if self.hub.options.price.price_aware and not self.hub.options.peaqev_lite:  # todo: strategy should handle this
            try:
                await self.hub.hours.async_update_max_min(
                    max_charge=self.hub.max_min_controller.max_charge,
                    session_energy=self.hub.chargecontroller.session.session_energy,
                    car_connected=self.hub.chargecontroller.connected,
                )
            except Exception as e:
                _LOGGER.debug(f"Unable to update max_min: {e}")

    @abstractmethod
    async def async_update_sensor_internal(self, entity, value) -> bool:
        pass

    @abstractmethod
    async def async_handle_outlet_updates(self):
        pass

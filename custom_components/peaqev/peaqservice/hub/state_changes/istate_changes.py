from __future__ import annotations

from typing import TYPE_CHECKING

from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.common.wait_timer import WaitTimer
from peaqevcore.services.scheduler.update_scheduler_dto import \
    UpdateSchedulerDTO

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

import logging
from abc import abstractmethod
from datetime import datetime

_LOGGER = logging.getLogger(__name__)


class StateChangesBase:
    latest_spotprice_update = WaitTimer(timeout=60)
    latest_outlet_update = WaitTimer(timeout=10)

    def __init__(self, hub: HomeAssistantHub, chargertype: ChargerType):
        self.hub = hub
        self.chargertype = chargertype

    async def async_update_sensor(self, entity, value):
        update_session = await self.async_update_sensor_internal(entity, value)
        await self.hub.observer.async_broadcast(ObserverTypes.ProcessChargeController)
        if self.hub.options.price.price_aware:  # todo: strategy should handle this
            await self.hub.observer.async_broadcast(ObserverTypes.ResetMaxMinChargeSensor)
            if entity != self.hub.spotprice.entity and (
                not self.hub.hours.is_initialized
                or self.latest_spotprice_update.is_timeout()
            ):
                """tweak to provoke spotprice to update more often"""
                self.latest_spotprice_update.update()
                await self.hub.spotprice.async_update_spotprice()

        await self.async_handle_sensor_attribute()
        await self.async_update_session_parameters(update_session)

        if all(
            [
                entity in self.hub.model.chargingtracker_entities,
                self.hub.is_initialized,
                self.chargertype is not ChargerType.NoCharger,  # todo: strategy should handle this
            ]
        ):
            await self.hub.observer.async_broadcast(ObserverTypes.ProcessCharger)

    async def async_update_session_parameters(self, update_session: bool) -> None:
        try:
            if all(
                [
                    self.hub.chargecontroller.charger.session_active,
                    update_session,
                    hasattr(self.hub.sensors, 'carpowersensor'),
                ]
            ):
                await self.hub.chargecontroller.session.async_set_session_energy(
                    getattr(self.hub.sensors.carpowersensor, 'value')
                )
                if self.hub.options.price.price_aware:  # todo: strategy should handle this
                    await self.hub.chargecontroller.session.async_set_session_price(
                        float(self.hub.spotprice.state)
                    )
            if getattr(self.hub.hours.scheduler, 'schedule_created', False):
                dto = UpdateSchedulerDTO(
                    moving_avg24=self.hub.sensors.powersensormovingaverage24.value,
                    peak=self.hub.current_peak_dynamic,
                    charged_amount=self.hub.chargecontroller.session.session_energy,
                    prices=self.hub.hours.prices,
                    prices_tomorrow=self.hub.hours.prices_tomorrow,
                    chargecontroller_state=self.hub.chargecontroller.status_type
                )
                await self.hub.hours.scheduler.async_update_facade(dto)
        except Exception as e:
            _LOGGER.exception(f'Unable to update session parameters: {e}')

    async def async_handle_sensor_attribute(self) -> None:
        if hasattr(self.hub.sensors, 'carpowersensor'):
            if self.hub.sensors.carpowersensor.use_attribute:  # todo: strategy should handle this
                entity = self.hub.sensors.carpowersensor
                try:
                    val = self.hub.state_machine.get_state(
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
                    _LOGGER.error(
                        f'Unable to get attribute-state for {entity.entity}|{entity.attribute}. {e}'
                    )

    async def async_update_chargerobject_switch(self, value) -> None:
        self.hub.sensors.chargerobject_switch.value = value
        await self.async_handle_outlet_updates()

    async def async_update_total_energy_and_peak(self, value) -> None:
        self.hub.sensors.totalhourlyenergy.value = value
        await self.hub.observer.async_broadcast(ObserverTypes.UpdatePeak, (float(value), datetime.now()))

        if self.hub.options.price.price_aware and not self.hub.options.peaqev_lite:  # todo: strategy should handle this
            try:
                await self.hub.hours.async_update_max_min(
                    max_charge=self.hub.max_min_controller.max_charge,
                    limiter=self.hub.max_min_controller.max_min_limiter,
                    session_energy=self.hub.chargecontroller.session.session_energy,
                    car_connected=self.hub.chargecontroller.connected,
                )
            except Exception as e:
                _LOGGER.error(f'Unable to update max_min: {e}')

    @abstractmethod
    async def async_update_sensor_internal(self, entity, value) -> bool:
        pass

    @abstractmethod
    async def async_handle_outlet_updates(self):
        pass

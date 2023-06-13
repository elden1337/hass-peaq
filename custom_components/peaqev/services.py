from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
    from homeassistant.core import HomeAssistant  # pylint: disable=import-error

import logging
from enum import Enum

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ServiceCalls(Enum):
    ENABLE = "enable"
    DISABLE = "disable"
    OVERRIDE_NONHOURS = "override_nonhours"
    SCHEDULER_SET = "scheduler_set"
    SCHEDULER_CANCEL = "scheduler_cancel"
    OVERRIDE_CHARGE_AMOUNT = "override_charge_amount"


async def async_prepare_register_services(hub: HomeAssistantHub, hass: HomeAssistant) -> None:
    async def async_servicehandler_enable(call):  # pylint:disable=unused-argument
        _LOGGER.debug("Calling {} service".format(ServiceCalls.ENABLE.value))
        await hub.servicecalls.async_call_enable_peaq()

    async def async_servicehandler_disable(call):  # pylint:disable=unused-argument
        _LOGGER.debug("Calling {} service".format(ServiceCalls.DISABLE.value))
        await hub.servicecalls.async_call_disable_peaq()

    async def async_servicehandler_override_nonhours(call):  # pylint:disable=unused-argument
        hours = call.data.get("hours")
        _LOGGER.debug("Calling {} service".format(ServiceCalls.OVERRIDE_NONHOURS.value))
        await hub.servicecalls.async_call_override_nonhours(1 if hours is None else hours)

    async def async_servicehandler_scheduler_set(call):  # pylint:disable=unused-argument
        charge_amount = call.data.get("charge_amount")
        departure_time = call.data.get("departure_time")
        schedule_starttime = call.data.get("schedule_starttime")
        override_settings = call.data.get("override_settings")
        _LOGGER.debug("Calling {} service".format(ServiceCalls.SCHEDULER_SET.value))
        await hub.servicecalls.async_call_schedule_needed_charge(
            charge_amount=charge_amount,
            departure_time=departure_time,
            schedule_starttime=schedule_starttime,
            override_settings=override_settings,
        )

    async def async_servicehandler_scheduler_cancel(call):
        _LOGGER.debug("Calling {} service".format(ServiceCalls.SCHEDULER_CANCEL.value))
        await hub.servicecalls.async_call_scheduler_cancel()

    async def async_servicehandler_override_charge_amount(call):
        _amount = call.data.get("desired_charge_amount")
        if hub.options.price.price_aware:
            _LOGGER.debug("Calling {} service".format(ServiceCalls.OVERRIDE_CHARGE_AMOUNT.value))
            if _amount and _amount > 0:
                await hub.max_min_controller.async_servicecall_override_charge_amount(_amount)
            else:
                await hub.max_min_controller.async_servicecall_reset_charge_amount()

    # Register services
    SERVICES = {
        ServiceCalls.ENABLE: async_servicehandler_enable,
        ServiceCalls.DISABLE: async_servicehandler_disable,
        ServiceCalls.OVERRIDE_NONHOURS: async_servicehandler_override_nonhours,
        ServiceCalls.SCHEDULER_SET: async_servicehandler_scheduler_set,
        ServiceCalls.SCHEDULER_CANCEL: async_servicehandler_scheduler_cancel,
        ServiceCalls.OVERRIDE_CHARGE_AMOUNT: async_servicehandler_override_charge_amount
    }

    for service, handler in SERVICES.items():
        hass.services.async_register(DOMAIN, service.value, handler)
    #_LOGGER.debug("Registered services: {}".format(SERVICES.keys()))

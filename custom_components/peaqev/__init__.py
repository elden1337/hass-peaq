"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pylint: disable=import-error

from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.util.constants import TYPELITE
from .const import (
    DOMAIN,
    PLATFORMS, LISTENER_FN_CLOSE
)
from .peaqservice.chargertypes.models.chargertypes_enum import ChargerType

_LOGGER = logging.getLogger(__name__)

from enum import Enum

class ServiceCalls(Enum):
    ENABLE = "enable"
    DISABLE = "disable"
    OVERRIDE_NONHOURS = "override_nonhours"
    SCHEDULER_SET = "scheduler_set"
    SCHEDULER_CANCEL = "scheduler_cancel"


async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Set up Peaqev"""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data
    options = await async_set_options(conf)
    hub = HomeAssistantHub(hass, options)
    hass.data[DOMAIN]["hub"] = hub
    await hub.setup()

    conf.async_on_unload(conf.add_update_listener(async_update_entry))

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
            override_settings=override_settings
        )

    async def async_servicehandler_scheduler_cancel(call):
        _LOGGER.debug("Calling {} service".format(ServiceCalls.SCHEDULER_CANCEL.value))
        await hub.servicecalls.async_call_scheduler_cancel()

    for platform in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(conf, platform))

    # Register services
    SERVICES = {
        ServiceCalls.ENABLE:            async_servicehandler_enable,
        ServiceCalls.DISABLE:           async_servicehandler_disable,
        ServiceCalls.OVERRIDE_NONHOURS: async_servicehandler_override_nonhours,
        ServiceCalls.SCHEDULER_SET:     async_servicehandler_scheduler_set,
        ServiceCalls.SCHEDULER_CANCEL:  async_servicehandler_scheduler_cancel
    }

    for service, handler in SERVICES.items():
        hass.services.async_register(DOMAIN, service.value, handler)

    return True


async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload Peaqev component when options changed."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_set_options(conf) -> HubOptions:
    options = HubOptions()

    options.peaqev_lite = bool(conf.data.get("peaqevtype") == TYPELITE)
    if options.peaqev_lite is False:
        options.powersensor = conf.data["name"]
    options.locale = conf.data.get("locale", "")
    options.charger.chargertype = conf.data.get("chargertype", "")
    if options.charger.chargertype == ChargerType.Outlet.value:
        options.charger.powerswitch = conf.data.get("outletswitch", "")
        options.charger.powermeter = conf.data.get("outletpowermeter", "")
    elif options.charger.chargertype != ChargerType.NoCharger.value:
        options.charger.chargerid = conf.data.get("chargerid", "")
    if options.charger.chargertype == ChargerType.NoCharger.value:
        options.powersensor_includes_car = True
    else:
        options.powersensor_includes_car = conf.data.get("powersensorincludescar", False)
    options.startpeaks = conf.options.get("startpeaks", conf.data.get("startpeaks"))
    options.cautionhours = await _async_get_existing_param(conf, "cautionhours", [])
    options.nonhours = await _async_get_existing_param(conf, "nonhours", [])
    options.price.price_aware = await _async_get_existing_param(conf, "priceaware", False)
    options.price.min_price = await _async_get_existing_param(conf, "min_priceaware_threshold_price", 0)
    options.price.top_price = await _async_get_existing_param(conf, "absolute_top_price", 0)
    options.price.dynamic_top_price = await _async_get_existing_param(conf, "dynamic_top_price", False)
    options.price.cautionhour_type = await _async_get_existing_param(conf, "cautionhour_type", "intermediate")
    options.fuse_type = await _async_get_existing_param(conf, "mains", "")
    options.blocknocturnal = await _async_get_existing_param(conf, "blocknocturnal", False)
    options.gainloss = await _async_get_existing_param(conf, "gainloss", False)
    return options


async def _async_get_existing_param(conf, parameter: str, default_val: any):
    return conf.options.get(parameter, conf.data.get(parameter, default_val))

"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry  # pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pylint: disable=import-error
from peaqevcore.hub.hub_options import HubOptions

from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.util.constants import TYPELITE
from .const import (
    DOMAIN,
    PLATFORMS, LISTENER_FN_CLOSE
)
from .peaqservice.chargertypes.models.chargertypes_enum import ChargerType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Set up Peaqev"""
    _LOGGER.debug("starting setup of Peaqev")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data

    options = await _set_options(conf)

    _LOGGER.debug("creating Hub")
    hub = HomeAssistantHub(hass, options, DOMAIN)
    _LOGGER.debug("Hub created")
    hass.data[DOMAIN]["hub"] = hub
    _LOGGER.debug("Hub setup start")
    await hub.setup()
    _LOGGER.debug("Hub setup done")

    conf.async_on_unload(conf.add_update_listener(async_update_entry))

    async def servicehandler_enable(call):  # pylint:disable=unused-argument
        await hub.servicecalls.call_enable_peaq()

    async def servicehandler_disable(call):  # pylint:disable=unused-argument
        await hub.servicecalls.call_disable_peaq()

    async def servicehandler_override_nonhours(call):  # pylint:disable=unused-argument
        hours = call.data.get("hours")
        await hub.servicecalls.call_override_nonhours(1 if hours is None else hours)

    async def servicehandler_scheduler_set(call):  # pylint:disable=unused-argument
        charge_amount = call.data.get("charge_amount")
        departure_time = call.data.get("departure_time")
        schedule_starttime = call.data.get("schedule_starttime")
        override_settings = call.data.get("override_settings")
        await hub.servicecalls.call_schedule_needed_charge(
            charge_amount=charge_amount,
            departure_time=departure_time,
            schedule_starttime=schedule_starttime,
            override_settings=override_settings
        )

    async def servicehandler_scheduler_cancel(call):
        await hub.servicecalls.call_scheduler_cancel()

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)
    hass.services.async_register(DOMAIN, "override_nonhours", servicehandler_override_nonhours)
    hass.services.async_register(DOMAIN, "scheduler_set", servicehandler_scheduler_set)
    hass.services.async_register(DOMAIN, "scheduler_cancel", servicehandler_scheduler_cancel)

    _LOGGER.debug("Sensors setup start")
    await hass.config_entries.async_forward_entry_setups(conf, PLATFORMS)
    _LOGGER.debug("Sensors setup done")

    return True


async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload Peaqev component when options changed."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def _set_options(conf) -> HubOptions:
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
    options.cautionhours = await _get_existing_param(conf, "cautionhours", [])
    options.nonhours = await _get_existing_param(conf, "nonhours", [])
    options.price.price_aware = await _get_existing_param(conf, "priceaware", False)
    options.price.min_price = await _get_existing_param(conf, "min_priceaware_threshold_price", 0)
    options.price.top_price = await _get_existing_param(conf, "absolute_top_price", 0)
    options.price.dynamic_top_price = await _get_existing_param(conf, "dynamic_top_price", False)
    options.price.cautionhour_type = await _get_existing_param(conf, "cautionhour_type", "intermediate")
    options.fuse_type = await _get_existing_param(conf, "mains", "")
    options.blocknocturnal = await _get_existing_param(conf, "blocknocturnal", False)
    return options


async def _get_existing_param(conf, parameter: str, default_val: any):
    return conf.options.get(parameter, conf.data.get(parameter, default_val))

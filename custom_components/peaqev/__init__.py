"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.hub.hub import Hub
from custom_components.peaqev.peaqservice.util.constants import TYPELITE
from .const import (
    DOMAIN,
    PLATFORMS, LISTENER_FN_CLOSE
)
from .peaqservice.hub.hub_lite import HubLite

#from .peaqservice.hub.models import ConfigModel

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Set up Peaq"""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data

    if "peaqevtype" in conf.data.keys():
        peaqtype_is_lite = bool(conf.data["peaqevtype"] == TYPELITE)
    else:
        peaqtype_is_lite = False

    ci = dict()

    ci["locale"] = conf.data["locale"]
    ci["chargertype"] = conf.data["chargertype"]
    ci["chargerid"] = conf.data["chargerid"]
    ci["startpeaks"] = conf.options["startpeaks"] if "startpeaks" in conf.options.keys() else conf.data["startpeaks"]
    ci["priceaware"] = await _get_existing_param(conf, "priceaware", False)
    ci["peaqtype_is_lite"] = peaqtype_is_lite

    if ci["priceaware"] is False:
        ci["cautionhours"] = conf.options["cautionhours"] if "cautionhours" in conf.options.keys() else conf.data["cautionhours"] if "cautionhours" in conf.data.keys() else []
        ci["nonhours"] = conf.options["nonhours"] if "nonhours" in conf.options.keys() else conf.data["nonhours"] if "nonhours" in conf.data.keys() else []
    else:
        ci["absolute_top_price"] = await _get_existing_param(conf, "absolute_top_price", 0)
        ci["min_price"] = await _get_existing_param(conf, "min_priceaware_threshold_price", 0)
        ci["cautionhour_type"] = conf.options["cautionhour_type"] if "cautionhour_type" in conf.options.keys() else conf.data["cautionhour_type"]
        ci["allow_top_up"] = await _get_existing_param(conf, "allow_top_up", False)

    if peaqtype_is_lite is True:
        hub = HubLite(hass, ci, DOMAIN)
    else:
        ci["powersensor"] = conf.data["name"]
        ci["powersensorincludescar"] = conf.data["powersensorincludescar"]

    """misc options"""
    ci["behavior_on_default"] = conf.options["behavior_on_default"] if "behavior_on_default" in conf.options.keys() else False

    unsub_options_update_listener = conf.add_update_listener(options_update_listener)
    ci["unsub_options_update_listener"] = unsub_options_update_listener

    hub = Hub(hass, ci, DOMAIN)
    hass.data[DOMAIN]["hub"] = hub

    async def servicehandler_enable(call):  # pylint:disable=unused-argument
        await hub.call_enable_peaq()

    async def servicehandler_disable(call):  # pylint:disable=unused-argument
        await hub.call_disable_peaq()

    async def servicehandler_override_nonhours(call):  # pylint:disable=unused-argument
        hours = call.data.get("hours")
        await hub.call_override_nonhours(1 if hours is None else hours)

    async def servicehandler_scheduler_set(call):  # pylint:disable=unused-argument
        charge_amount = call.data.get("charge_amount")
        departure_time = call.data.get("departure_time")
        schedule_starttime = call.data.get("schedule_starttime")
        override_settings = call.data.get("override_settings")
        await hub.call_schedule_needed_charge(
            charge_amount=charge_amount,
            departure_time=departure_time,
            schedule_starttime=schedule_starttime,
            override_settings=override_settings
        )

    async def servicehandler_scheduler_cancel(call):
        await hub.call_scheduler_cancel()

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)
    hass.services.async_register(DOMAIN, "override_nonhours", servicehandler_override_nonhours)
    hass.services.async_register(DOMAIN, "scheduler_set", servicehandler_scheduler_set)
    hass.services.async_register(DOMAIN, "scheduler_cancel", servicehandler_scheduler_cancel)
    hass.config_entries.async_setup_platforms(conf, PLATFORMS)

    return True

async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = hass.config_entries.async_unload_platforms(conf, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(conf.entry_id)
    return unload_ok


async def _get_existing_param(conf, parameter: str, default_val: any):
    if parameter in conf.options.keys():
        return conf.options.get(parameter)
    if parameter in conf.data.keys():
        return conf.data.get(parameter)
    return default_val


# async def _set_configuration_model(self, conf) -> ConfigModel:
#     if "peaqevtype" in conf.data.keys():
#         peaqtype_is_lite = bool(conf.data["peaqevtype"] == TYPELITE)
#     else:
#         peaqtype_is_lite = False
#
#     model = ConfigModel()
#     model.locale = conf.data["locale"]
#     model.chargertype = conf.data["chargertype"]
#     model.chargerid = conf.data["chargerid"]
#     model.startpeaks = conf.options["startpeaks"] if "startpeaks" in conf.options.keys() else conf.data["startpeaks"]
#     model.hours.priceaware = await _get_existing_param(conf, "priceaware", False)
#     model.lite = peaqtype_is_lite
#
#     if model.priceaware is False:
#         model.hours.cautionhours = conf.options["cautionhours"] if "cautionhours" in conf.options.keys() else conf.data["cautionhours"] if "cautionhours" in conf.data.keys() else []
#         model.hours.nonhours = conf.options["nonhours"] if "nonhours" in conf.options.keys() else conf.data["nonhours"] if "nonhours" in conf.data.keys() else []
#     else:
#         model.hours.absolute_top_price = await _get_existing_param(conf, "absolute_top_price", 0)
#         model.hours.min_price = await _get_existing_param(conf, "min_priceaware_threshold_price", 0)
#         model.hours.cautionhour_type = conf.options["cautionhour_type"] if "cautionhour_type" in conf.options.keys() else conf.data["cautionhour_type"]
#         model.hours.allow_top_up = await _get_existing_param(conf, "allow_top_up", False)
#
#     if peaqtype_is_lite is True:
#         return model
#     else:
#         model.powersensor = conf.data["name"]
#         model.powersensorincludescar = conf.data["powersensorincludescar"]
#
#     """misc options"""
#     model.options.behavior_on_default = conf.options["behavior_on_default"] if "behavior_on_default" in conf.options.keys() else False
#
#     return model

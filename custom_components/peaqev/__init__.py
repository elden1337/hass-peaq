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

_LOGGER = logging.getLogger(__name__)


async def _get_existing_param(conf, parameter: str, default_val: any):
    if parameter in conf.options.keys():
        return conf.options.get(parameter)
    if parameter in conf.data.keys():
        return conf.data.get(parameter)
    return default_val

async def async_setup_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Set up Peaq"""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][conf.entry_id] = conf.data

    if "peaqevtype" in conf.data.keys():
        peaqtype_is_lite = bool(conf.data["peaqevtype"] == TYPELITE)

    else:
        peaqtype_is_lite = False

    ci = {}

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

        hub = Hub(hass, ci, DOMAIN)

    hass.data[DOMAIN]["hub"] = hub

    async def servicehandler_enable(call): # pylint:disable=unused-argument
        await hub.call_enable_peaq()

    async def servicehandler_disable(call): # pylint:disable=unused-argument
        await hub.call_disable_peaq()

    ATTR_HOURS = "hours"
    async def servicehandler_override_nonhours(call): # pylint:disable=unused-argument
        try:
            hours = call.data.get(ATTR_HOURS)
        except:
            hours = 1
        await hub.call_override_nonhours(hours)

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)
    hass.services.async_register(DOMAIN, "override_nonhours", servicehandler_override_nonhours)

    hass.config_entries.async_setup_platforms(conf, PLATFORMS)

    undo_listener = conf.add_update_listener(config_entry_update_listener)

    hass.data[DOMAIN][conf.entry_id] = {
        LISTENER_FN_CLOSE: undo_listener,
    }
    return True

async def config_entry_update_listener(hass: HomeAssistant, conf: ConfigEntry):
    _LOGGER.debug("Trying to reboot after options-change.")
    await hass.config_entries.async_reload(conf.entry_id)

async def async_unload_entry(hass: HomeAssistant, conf: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = hass.config_entries.async_unload_platforms(conf, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(conf.entry_id)

    return unload_ok

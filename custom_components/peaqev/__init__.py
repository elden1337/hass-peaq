"""The peaqev integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.hub.hub import Hub
from custom_components.peaqev.peaqservice.util.constants import TYPELITE
from .const import (
    DOMAIN,
    PLATFORMS
)
from .peaqservice.hub.hub_lite import HubLite

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up Peaq"""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config.entry_id] = config.data

    if "peaqevtype" in config.data.keys():
        peaqtype_is_lite = bool(config.data["peaqevtype"] == TYPELITE)

    else:
        peaqtype_is_lite = False

    configinputs = {}

    configinputs["locale"] = config.data["locale"]
    configinputs["chargertype"] = config.data["chargertype"]
    configinputs["chargerid"] = config.data["chargerid"]
    configinputs["startpeaks"] = config.data["startpeaks"]
    configinputs["priceaware"] = config.data["priceaware"]
    configinputs["peaqtype_is_lite"] = peaqtype_is_lite

    if config.data["priceaware"] is False:
        configinputs["cautionhours"] = config.data["cautionhours"]
        configinputs["nonhours"] = config.data["nonhours"]
    else:
        configinputs["absolute_top_price"] = config.data["absolute_top_price"]
        configinputs["cautionhour_type"] = config.data["cautionhour_type"]

    if peaqtype_is_lite is True:
        hub = HubLite(hass, configinputs, DOMAIN)
    else:
        configinputs["powersensor"] = config.data["name"]
        configinputs["powersensorincludescar"] = config.data["powersensorincludescar"]

        hub = Hub(hass, configinputs, DOMAIN)

    hass.data[DOMAIN]["hub"] = hub

    async def servicehandler_enable(call):
        await hub.call_enable_peaq()

    async def servicehandler_disable(call):
        await hub.call_disable_peaq()

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)

    hass.config_entries.async_setup_platforms(config, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

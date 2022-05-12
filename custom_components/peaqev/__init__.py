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

    if config.data["peaqevtype"] == TYPELITE:
        configinputs = {
            "locale": config.data["locale"],
            "chargertype": config.data["chargertype"],
            "chargerid": config.data["chargerid"],
            "cautionhours": config.data["cautionhours"] if "cautionhors" in config.data.keys() else [],
            "nonhours": config.data["nonhours"] if "nonhours" in config.data.keys() else [],
            "startpeaks": config.data["startpeaks"],
            "priceaware": config.data["priceaware"],
            "absolute_top_price": config.data["absolute_top_price"],
            "cautionhour_type": config.data["cautionhour_type"]
        }

        hub = HubLite(hass, configinputs, DOMAIN)
    else:
        configinputs = {
            "powersensor": config.data["name"],
            "powersensorincludescar": config.data["powersensorincludescar"],
            "locale": config.data["locale"],
            "chargertype": config.data["chargertype"],
            "chargerid": config.data["chargerid"],
            "cautionhours": config.data["cautionhours"] if "cautionhors" in config.data.keys() else [],
            "nonhours": config.data["nonhours"] if "nonhours" in config.data.keys() else [],
            "startpeaks": config.data["startpeaks"],
            "priceaware": config.data["priceaware"],
            "absolute_top_price": config.data["absolute_top_price"],
            "cautionhour_type": config.data["cautionhour_type"]
        }

        hub = Hub(hass, configinputs, DOMAIN)

    await hub.is_initialized()
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

"""The peaqev integration."""
from __future__ import annotations
import logging
from custom_components.peaqev.peaqservice.hub.hub import Hub
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .peaqservice.hub.hub_lite import HubLite

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    PLATFORMS
    )

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:   
    """Set up Peaq"""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config.entry_id] = config.data

    configinputs = {
        "powersensor": config.data["name"],
        "powersensorincludescar": config.data["powersensorincludescar"],
        "locale": config.data["locale"],
        "chargertype": config.data["chargertype"],
        "chargerid": config.data["chargerid"],
        "cautionhours": config.data["cautionhours"] if "cautionhors" in config.data.keys() else [] ,
        "nonhours": config.data["nonhours"] if "nonhours" in config.data.keys() else [],
        "startpeaks": config.data["startpeaks"],
        "priceaware": config.data["priceaware"],
        "absolute_top_price": config.data["absolute_top_price"],
        "cautionhour_type": config.data["cautionhour_type"]
    }

    if config.data["peaqlite"] is True:
        hub = HubLite(hass, configinputs, DOMAIN)
    else:
        hub = Hub(hass, configinputs, DOMAIN)

    await hub.is_initialized()
    hass.data[DOMAIN]["hub"] = hub
    
    """Create Service calls"""
    async def servicehandler_enable(call):
        await hub.call_enable_peaq()

    async def servicehandler_disable(call):
        await hub.call_disable_peaq()

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)
    """/Create Service calls"""

    hass.config_entries.async_setup_platforms(config, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

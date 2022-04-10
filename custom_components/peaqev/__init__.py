"""The peaqev integration."""
from __future__ import annotations
import logging
from custom_components.peaqev.peaqservice.hub import Hub
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
        "cautionhours": config.data["options"]["cautionhours"],
        "chargerid": config.data["chargerid"],
        "nonhours": config.data["options"]["nonhours"],
        "monthlystartpeak": config.data["options"]["startpeaks"]
    }

    hub = Hub(hass, configinputs, DOMAIN)
    await hub.is_initialized()
    hass.data[DOMAIN]["hub"] = hub
    
    """Create Service calls"""
    async def servicehandler_enable(call):
        hub.charger_enabled.value = "on"
        hub.charger_done.value = "off"
    async def servicehandler_disable(call):
        hub.charger_enabled.value = "off"

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)
    """/Create Service calls"""

    hass.config_entries.async_setup_platforms(config, PLATFORMS)

    return True

def unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
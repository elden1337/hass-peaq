"""The peaq integration."""
from __future__ import annotations
import logging
from custom_components.peaq.peaq.hub import Hub
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    PLATFORMS,
    DOMAIN_DATA
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
        "cautionhours" : [11,18,19],
        "nonhours": [12,16,17],
        "monthlystartpeak": {1: 2.0, 2: 1.8, 3: 1.8, 4: 1.5, 5: 1.5, 6: 1.5, 7: 1.5, 8: 1.5, 9: 1.5, 10: 1.5, 11:1.8, 12: 2.0}    
    }

    hub = Hub(hass, configinputs)
    hass.data[DOMAIN]["hub"] = hub
    
    """SERVICE CALLS"""
    async def servicehandler_enable(call):
        hass.states.async_set("binary_sensor.peaq_charger_enabled", "on")
    async def servicehandler_disable(call):
        hass.states.async_set("binary_sensor.peaq_charger_enabled", "off")

    hass.services.async_register(DOMAIN, "enable", servicehandler_enable)
    hass.services.async_register(DOMAIN, "disable", servicehandler_disable)

    hass.config_entries.async_setup_platforms(config, PLATFORMS)

    return True

def unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
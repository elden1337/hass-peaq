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
        "monthlystartpeak": config.data["options"]["startpeaks"],
        #"cautionhours" : [11,18,19],
        #"nonhours": [12,16,17],
        #"monthlystartpeak": {1: 2.0, 2: 1.8, 3: 1.8, 4: 1.5, 5: 1.5, 6: 1.5, 7: 1.5, 8: 1.5, 9: 1.5, 10: 1.5, 11:1.8, 12: 2.0}    
    }

    hub = Hub(hass, configinputs, DOMAIN)
    await hub.initialize()
    hass.data[DOMAIN]["hub"] = hub
    
    """Create Service calls"""
    async def servicehandler_enable(call):
        hub.charger_enabled.value = "on"
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
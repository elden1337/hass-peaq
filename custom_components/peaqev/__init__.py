"""The peaqev integration."""
from __future__ import annotations
import logging
from custom_components.peaqev.peaqservice.hub.hub import Hub
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

    _standard_startpeaks = {1: 1.5, 2: 1.5, 3: 1.5, 4: 1.5, 5: 1.5, 6: 1.5, 7: 1.5, 8: 1.5, 9: 1.5, 10: 1.5, 11: 1.5, 12: 1.5}

    configinputs = {
        "powersensor": config.data["name"],
        "powersensorincludescar": config.data["powersensorincludescar"],
        "locale": config.data["locale"],
        "chargertype": config.data["chargertype"],
        "chargerid": config.data["chargerid"],
        "cautionhours": config.options["cautionhours"] if "cautionhours" in config.options.keys() else config.data["options"]["cautionhours"] if "cautionhours" in config.data["options"].keys() else [],
        "nonhours": config.options["nonhours"] if "nonhours" in config.options.keys() else config.data["options"]["nonhours"] if "nonhours" in config.data["options"].keys() else [],
        "monthlystartpeak": config.options["startpeaks"] if "startpeaks" in config.options.keys() else config.data["options"]["startpeaks"] if "startpeaks" in config.data["options"].keys() else _standard_startpeaks,
        "priceaware": config.options["priceaware"] if "priceaware" in config.options.keys() else False,
        "absolute_top_price": config.options["absolute_top_price"] if "absolute_top_price" in config.options.keys() else None,
        "cautionhour_type": config.options["cautionhour_type"] if "cautionhour_type" in config.options.keys() else 0
    }

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

def unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
"""Config flow for Peaq integration."""
from __future__ import annotations
import logging
import voluptuous as vol
from typing import Any, Optional
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.peaqev.peaqservice.util.constants as pk
# from homeassistant.helpers.entity_registry import (
#     async_entries_for_config_entry,
#     async_get_registry,
# )

from .const import DOMAIN   # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,  
        vol.Optional("powersensorincludescar", default=False): cv.boolean, 
        vol.Optional(
            "chargertype",
            default="",
            ): vol.In(pk.CHARGERTYPES),
        vol.Optional("chargerid"): cv.string,
        vol.Optional(
            "locale",
            default="",
            ): vol.In(pk.LOCALES)
    }
)


async def _check_power_sensor(hass: HomeAssistant, powersensor:str) -> bool:
    ret = hass.states.get(powersensor)
    try:
        float(ret)
        return True
    except:
        return False


async def validate_input_user(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """ Validate the data can be used to set up a connection."""

    if len(data["chargerid"]) < 3:
        raise ValueError

    if len(data["name"]) < 3:
        raise ValueError
    elif not data["name"].startswith("sensor."):
        data["name"] = f"sensor.{data['name']}"
    if await _check_power_sensor(hass, data["name"]) is False:
        raise ValueError

    return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Peaq."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        
        errors = {}
        if user_input is not None:
            try:
                self.info = await validate_input_user(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_setup"
            if not errors:
                self.data = user_input
                self.data[self.OPTIONS] = []

                return await self.async_step_opt()

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_opt(self, user_input = None):
        """Second step in config flow to add options"""
        
        errors = {}
        if user_input is not None:
            # if not errors:
                # Input is valid, set data.
            self.data[self.OPTIONS]= {
                "nonhours": user_input["nonhours"],
                "cautionhours": user_input["cautionhours"]
            }
                
            return await self.async_step_startmonth()
        
        mockhours = [h for h in range(0, 24)]

        OPT_SCHEMA = vol.Schema(
        {
           vol.Optional("nonhours", default=list(mockhours)): cv.multi_select(
               mockhours
                ),
                vol.Optional("cautionhours", default=list(mockhours)): cv.multi_select(
                    mockhours
                )
        })

        return self.async_show_form(
            step_id="opt", data_schema=OPT_SCHEMA, errors=errors
        )

    async def async_step_startmonth(self, user_input = None):
        """Second step in config flow to add options"""
        
        errors = {}
        if user_input is not None:
            # if not errors:
                # Input is valid, set data.
            self.data[self.OPTIONS]["startpeaks"]= await self._set_startpeak_dict(user_input)
                
            return self.async_create_entry(title=self.info["title"], data=self.data)
        
        OPT_SCHEMA = vol.Schema(
        {
           vol.Optional("jan", default=1.5): cv.positive_float,
           vol.Optional("feb", default=1.5): cv.positive_float,
           vol.Optional("mar", default=1.5): cv.positive_float,
           vol.Optional("apr", default=1.5): cv.positive_float,
           vol.Optional("may", default=1.5): cv.positive_float,
           vol.Optional("jun", default=1.5): cv.positive_float,
           vol.Optional("jul", default=1.5): cv.positive_float,
           vol.Optional("aug", default=1.5): cv.positive_float,
           vol.Optional("sep", default=1.5): cv.positive_float,
           vol.Optional("oct", default=1.5): cv.positive_float,
           vol.Optional("nov", default=1.5): cv.positive_float,
           vol.Optional("dec", default=1.5): cv.positive_float
        })

        return self.async_show_form(
            step_id="startmonth", data_schema=OPT_SCHEMA, errors=errors
        )

    async def _set_startpeak_dict(self, user_input) -> dict:
        ret = {}
        ret[1] = user_input["jan"]
        ret[2] = user_input["feb"]
        ret[3] = user_input["mar"]
        ret[4] = user_input["apr"]
        ret[5] = user_input["may"]
        ret[6] = user_input["jun"]
        ret[7] = user_input["jul"]
        ret[8] = user_input["aug"]
        ret[9] = user_input["sep"]
        ret[10] = user_input["oct"]
        ret[11] = user_input["nov"]
        ret[12] = user_input["dec"]
        return ret


class InvalidChargerId(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class InvalidPowerSensor(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

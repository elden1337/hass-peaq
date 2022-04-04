"""Config flow for Peaq integration."""
from __future__ import annotations
import logging
import voluptuous as vol
#from copy import deepcopy
from typing import Any, Optional
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.peaqev.peaqservice.constants as pk
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

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """ Validate the data can be used to set up a connection."""

    #if type is chargeamps or easee
        #check if chargerid is set. otherwise be angry.


    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    # if len(data["host"]) < 3:
    #     raise InvalidHost

    # hub = Hub(hass, data["host"])
    # result = await hub.test_connection()
    # if not result:
    #     raise CannotConnect

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    return {"title": data["name"]}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Peaq."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data : Optional[dict[str,Any]]
    info : Optional[dict[str,Any]]

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        
        errors = {}
        if user_input is not None:
            # try:
                self.info = await validate_input(self.hass, user_input)
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
           vol.Optional("jan", default=1.5): cv.float(),
           vol.Optional("feb", default=1.5): cv.float(),
           vol.Optional("mar", default=1.5): cv.float(),
           vol.Optional("apr", default=1.5): cv.float(),
           vol.Optional("may", default=1.5): cv.float(),
           vol.Optional("jun", default=1.5): cv.float(),
           vol.Optional("jul", default=1.5): cv.float(),
           vol.Optional("aug", default=1.5): cv.float(),
           vol.Optional("sep", default=1.5): cv.float(),
           vol.Optional("oct", default=1.5): cv.float(),
           vol.Optional("nov", default=1.5): cv.float(),
           vol.Optional("dec", default=1.5): cv.float(),
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

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

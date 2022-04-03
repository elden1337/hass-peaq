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
                #return self.async_create_entry(title=info["title"], data=self.data)

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
                
                # User is done adding repos, create the config entry.
            return self.async_create_entry(title=self.info["title"], data=self.data)
        
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

    #async def async_step_startmonth(self, user_input=None):
    #    """Second step in config flow to add options"""

   #     errors = {}
    #    if user_input is not None:
            # if not errors:
            # Input is valid, set data.
     #       self.data[self.OPTIONS] = {
      #          "nonhours": user_input["nonhours"],
       #         "cautionhours": user_input["cautionhours"]
        #    }

            # User is done adding repos, create the config entry.
      #      return self.async_create_entry(title=self.info["title"], data=self.data)

        #mockhours = [h for h in range(0, 24)]

        #OPT_SCHEMA = vol.Schema(
         #   {
          #      vol.Optional("nonhours", default=list(mockhours)): cv.multi_select(
           #         mockhours
            #    ),
             #   vol.Optional("cautionhours", default=list(mockhours)): cv.multi_select(
              #      mockhours
               # )
            #})

        #return self.async_show_form(step_id="startmonth", data_schema=OPT_SCHEMA, errors=errors)

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Get the options flow for this handler."""
    #     return OptionsFlowHandler(config_entry)

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

# class OptionsFlowHandler(config_entries.OptionsFlow):
#     """Handles options flow for the component."""

#     def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
#         self.config_entry = config_entry

#     async def async_step_init(
#         self, user_input: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """Manage the options for the custom component."""
#         errors: Dict[str, str] = {}
#         # Grab all configured repos from the entity registry so we can populate the
#         # multi-select dropdown that will allow a user to remove a repo.
#         entity_registry = await async_get_registry(self.hass)
        
#         # entries = async_entries_for_config_entry(
#         #     entity_registry, self.config_entry.entry_id
#         # )
#         # Default value for our multi-select.
#         # all_repos = {e.entity_id: e.original_name for e in entries}
#         # repo_map = {e.entity_id: e for e in entries}
#         nonhours_map = []
#         cautionhours_map = []

#         saved_nonhours = {}
#         saved_cautionhours = {}

#         if user_input is not None:
#             #updated_repos = deepcopy(self.config_entry.data[CONF_REPOS])
#             updated_nonhours = deepcopy(self.config_entry.data["nonhours"])
#             updated_cautionhours = deepcopy(self.config_entry.data["cautionhours"])

#             # Remove any unchecked repos.
#             removed_nonhours = [
#                 entity_id
#                 for entity_id in nonhours_map
#                 if entity_id not in user_input["nonhours"]
#             ]
#             removed_cautionhours = [
#                 entity_id
#                 for entity_id in cautionhours_map
#                 if entity_id not in user_input["cautionhours"]
#             ]
            
#             for h in removed_nonhours:
#                 # Unregister from HA
#                 entity_registry.async_remove(h)
#                 # Remove from our configured repos.
#                 entry = nonhours_map[h]
#                 entry_path = entry.unique_id
#                 updated_nonhours = [e for e in updated_nonhours if e["path"] != entry_path]

#             for h in removed_cautionhours:
#                 # Unregister from HA
#                 entity_registry.async_remove(h)
#                 # Remove from our configured repos.
#                 entry = cautionhours_map[h]
#                 entry_path = entry.unique_id
#                 updated_cautionhours = [e for e in updated_cautionhours if e["path"] != entry_path]

#             # if user_input.get(CONF_PATH):
#             #     # Validate the path.
#             #     access_token = self.hass.data[DOMAIN][self.config_entry.entry_id][
#             #         CONF_ACCESS_TOKEN
#             #     ]
#             #     try:
#             #         await validate_path(user_input[CONF_PATH], access_token, self.hass)
#             #     except ValueError:
#             #         errors["base"] = "invalid_path"

#             #     if not errors:
            
#             # Add the new repo.
#             updated_nonhours.append(
#                 user_input["nonhours"]
#             )
#             updated_cautionhours.append(
#                 user_input["cautionhours"]
#             )
#                     # updated_repos.append(
#                     #     {
#                     #         "path": user_input[CONF_PATH],
#                     #         "name": user_input.get(CONF_NAME, user_input[CONF_PATH]),
#                     #     }
#                     # )

#             if not errors:
#                 # Value of data will be set on the options property of our config_entry
#                 # instance.
#                 return self.async_create_entry(
#                     title="",
#                     data={
#                         "nonhours": updated_nonhours,
#                         "cautionhours": updated_cautionhours
#                         },
#                 )

#         mockhours = [h for h in range(0,24)]

#         options_schema = vol.Schema(
#             {
#                 vol.Optional("nonhours", default=list(mockhours)): cv.multi_select(
#                     saved_nonhours
#                 ),
#                 vol.Optional("cautionhours", default=list(mockhours)): cv.multi_select(
#                     saved_cautionhours
#                 )
#                 # ,
#                 # vol.Optional("jan"): cv.float,
#                 # vol.Optional("feb"): cv.float,
#                 # vol.Optional("mar"): cv.float,
#                 # vol.Optional("apr"): cv.float,
#                 # vol.Optional("may"): cv.float,
#                 # vol.Optional("jun"): cv.float,
#                 # vol.Optional("jul"): cv.float,
#                 # vol.Optional("aug"): cv.float,
#                 # vol.Optional("sep"): cv.float,
#                 # vol.Optional("oct"): cv.float,
#                 # vol.Optional("nov"): cv.float,
#                 # vol.Optional("dec"): cv.float
#             }
#         )
#         return self.async_show_form(
#             step_id="init", data_schema=options_schema, errors=errors
#         )
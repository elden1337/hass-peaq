"""Config flow for Peaq integration."""
from __future__ import annotations
import logging
from copy import deepcopy
from typing import Any, Dict, Optional
import voluptuous as vol
from typing import Any, Optional
from homeassistant import config_entries, exceptions
from homeassistant.core import (HomeAssistant, callback)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.peaqev.peaqservice.util.constants as pk
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)

from .const import DOMAIN   # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

INIT_SCHEMA = vol.Schema(
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

STARTMONTHS_SCHEMA = vol.Schema(
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


async def _check_power_sensor(hass: HomeAssistant, powersensor:str) -> bool:
    ret = hass.states.get(powersensor).state
    try:
        float(ret)
        return True
    except:
        msg = f"{powersensor} did not produce a valid state for {DOMAIN}. State was {ret}"
        _LOGGER.error(msg)
        return False


async def _validate_input_first(hass: HomeAssistant, data: dict) -> dict[str, Any]:
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


async def _validate_input_first_chargerid(data: dict) -> dict[str, Any]:
    """ Validate the chargerId"""
    if len(data["chargerid"]) < 1:
        raise ValueError

    return {"title": data["name"]}


async def _validate_nonhours(data: dict) -> dict[str, Any]:
    """ Validate nonhour-length"""
    if len(data["nonhours"]) == 24:
        raise ValueError

    return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Peaq."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

    async def async_step_first(self, user_input=None):
        """Handle the initial step."""
        
        errors = {}
        if user_input is not None:
            try:
                self.info = await _validate_input_first(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_powersensor"
            try:
                self.info = await _validate_input_first(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_chargerid"
            if not errors:
                self.data = user_input
                self.data[self.OPTIONS] = []

                return await self.async_step_startmonth()

        return self.async_show_form(
            step_id="user", data_schema=INIT_SCHEMA, errors=errors
        )

    # async def async_step_second(self, user_input = None):
    #     """Second step in config flow to add options"""
    #
    #     errors = {}
    #     if user_input is not None:
    #         try:
    #             await _validate_nonhours(user_input)
    #         except ValueError:
    #             errors["base"] = "invalid_nonhours"
    #         if not errors:
    #             self.data[self.OPTIONS] = {
    #                 "nonhours": user_input["nonhours"],
    #                 "cautionhours": user_input["cautionhours"]
    #             }
    #
    #             return await self.async_step_startmonth()
    #
    #     mockhours = [h for h in range(0, 24)]
    #
    #     OPT_SCHEMA = vol.Schema(
    #     {
    #         vol.Optional("nonhours", default=list(mockhours)): cv.multi_select(
    #            mockhours
    #             ),
    #         vol.Optional("cautionhours", default=list(mockhours)): cv.multi_select(
    #             mockhours
    #         ),
    #         vol.Optional("priceaware", default=False): cv.boolean
    #     })
    #
    #     return self.async_show_form(
    #         step_id="opt", data_schema=OPT_SCHEMA, errors=errors
    #     )

    async def async_step_startmonth(self, user_input = None):
        """Second step in config flow to add options"""
        
        errors = {}
        if user_input is not None:
            # if not errors:
                # Input is valid, set data.
            self.data[self.OPTIONS]["startpeaks"] = await self._set_startpeak_dict(user_input)
                
            return self.async_create_entry(title=self.info["title"], data=self.data)
        


        return self.async_show_form(
            step_id="startmonth", data_schema=STARTMONTHS_SCHEMA, errors=errors
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        # Grab all configured repos from the entity registry so we can populate the
        # multi-select dropdown that will allow a user to remove a repo.
        entity_registry = await async_get_registry(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        # Default value for our multi-select.
        all_repos = {e.entity_id: e.original_name for e in entries}
        repo_map = {e.entity_id: e for e in entries}

        if user_input is not None:
            updated_repos = deepcopy(self.config_entry.data[CONF_REPOS])

            # Remove any unchecked repos.
            removed_nonhours = [
                entity_id
                for entity_id in repo_map.keys()
                if entity_id not in user_input["nonhours"]
            ]

            removed_cautionhours = [
                entity_id
                for entity_id in repo_map.keys()
                if entity_id not in user_input["cautionhours"]
            ]

            for hour in removed_nonhours:
                entity_registry.async_remove(hour)
                # Remove from our configured repos.
                #entry = repo_map[hour]
                #entry_path = entry.unique_id
                #updated_repos = [e for e in updated_repos if e["path"] != entry_path]
            for hour in removed_cautionhours:
                entity_registry.async_remove(hour)

            if user_input.get(CONF_PATH):
                # Validate the path.
                # access_token = self.hass.data[DOMAIN][self.config_entry.entry_id][
                #     CONF_ACCESS_TOKEN
                # ]
                # try:
                #     await validate_path(user_input[CONF_PATH], access_token, self.hass)
                # except ValueError:
                #     errors["base"] = "invalid_path"

                if not errors:
                    # Add the new repo.
                    updated_repos.append(
                        {
                            "path": user_input[CONF_PATH],
                            "name": user_input.get(CONF_NAME, user_input[CONF_PATH]),
                        }
                    )

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={CONF_REPOS: updated_repos},
                )

        mockhours = [h for h in range(0, 24)]

        #this one is just here to transfer existing installations into options-flow.
        _transfer_nonhours = self.config_entry.data["options"]["nonhours"]
        if _transfer_nonhours is None or len(_transfer_nonhours) == 0:
            _transfer_nonhours = mockhours

        # this one is just here to transfer existing installations into options-flow.
        _transfer_cautionhours = self.config_entry.data["options"]["cautionhours"]
        if _transfer_cautionhours is None or len(_transfer_cautionhours) == 0:
            _transfer_cautionhours = mockhours


        OPT_SCHEMA = vol.Schema(
            {
                vol.Optional("nonhours", default=list(_transfer_nonhours)): cv.multi_select(
                    mockhours
                ),
                vol.Optional("cautionhours", default=list(_transfer_cautionhours)): cv.multi_select(
                    mockhours
                ),
                vol.Optional("priceaware", default=False): cv.boolean,
                vol.Optional("absolute_top_price"): cv.positive_float
            })

        return self.async_show_form(
            step_id="init", data_schema=OPT_SCHEMA, errors=errors
        )

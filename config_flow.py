"""Config flow for Compare It integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.peaq.peaq.constants as pk

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA =  vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,  
        vol.Optional("powersensorincludescar", default=False): cv.boolean, 
        vol.Optional(
            "chargertype",
            default="",
            ): vol.In(pk.CHARGERTYPES),
        vol.Optional(
            "locale",
            default="",
            ): vol.In(pk.LOCALES)
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    # Validate the data can be used to set up a connection.

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
    """Handle config flow for peaq."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        
        errors = {}
        if user_input is not None:
            # try:
                _LOGGER.info(f"peaq: {user_input}")
                info = await validate_input(self.hass, user_input)
                self.data = user_input

                return self.async_create_entry(title=info["title"], data=self.data)
            # except CannotConnect:
            #     errors["base"] = "cannot_connect"
            # except InvalidHost:
            #     errors["username"] = "cannot_connect"
            # except Exception:  # pylint: disable=broad-except
            #     _LOGGER.exception("Unexpected exception")
            #     errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
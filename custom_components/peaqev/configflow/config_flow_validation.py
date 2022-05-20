import logging

from homeassistant import exceptions
from homeassistant.core import HomeAssistant
from typing import Any

import custom_components.peaqev.peaqservice.util.extensionmethods as ex

_LOGGER = logging.getLogger(__name__)

class ConfigFlowValidation:

    @staticmethod
    async def validate_power_sensor(hass: HomeAssistant, powersensor: str) -> bool:
        val_state = hass.states.get(powersensor)
        ret = ex.try_parse(val_state.state, float)
        if ret is False:
            raise FaultyPowerSensor

        return True

    @staticmethod
    async def validate_input_first(data: dict) -> dict[str, Any]:
        """ Validate the data can be used to set up a connection."""

        if len(data["name"]) < 3:
            raise ValueError
        if not data["name"].startswith("sensor."):
            data["name"] = f"sensor.{data['name']}"
        #if await _check_power_sensor(hass, data["name"]) is False:
        #    raise ValueError

        return {"title": data["name"]}

    @staticmethod
    async def validate_input_first_chargerid(data: dict) -> dict[str, Any]:
        """ Validate the chargerId"""
        #if len(data["chargerid"]) < 1:
        #    raise ValueError

        return {"title": data["name"]}


class FaultyPowerSensor(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
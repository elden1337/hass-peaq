import logging
from typing import Any

from homeassistant import exceptions
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ConfigFlowValidation:
    @staticmethod
    async def validate_power_sensor(hass: HomeAssistant, powersensor: str):
        _powersensor = (
            f"sensor.{powersensor}"
            if not powersensor.startswith("sensor.")
            else powersensor
        )
        val_state = hass.states.get(_powersensor)
        if val_state is None:
            _LOGGER.error(
                f"Could not validate chosen powersensor {_powersensor}. It returned None as state."
            )
            raise FaultyPowerSensor
        elif not isinstance(float(val_state.state), float):
            _LOGGER.error(
                f"Could not validate chosen powersensor {_powersensor}. The value of its state is not a number. {val_state.state}"
            )
            raise FaultyPowerSensor

    @staticmethod
    async def validate_input_first(data: dict) -> dict[str, Any]:
        if len(data["name"]) < 3:
            raise ValueError
        if not data["name"].startswith("sensor."):
            data["name"] = f"sensor.{data['name']}"
        return {"title": data["name"]}

    @staticmethod
    async def validate_input_first_chargerid(data: dict) -> dict[str, Any]:
        """Validate the chargerId"""
        # if len(data["chargerid"]) < 1:
        #    raise ValueError

        return {"title": data["name"]}


class FaultyPowerSensor(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

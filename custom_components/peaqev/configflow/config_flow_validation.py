import logging
from typing import Any

from homeassistant import exceptions
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ConfigFlowValidation:
    @staticmethod
    async def validate_power_sensor(hass: HomeAssistant, powersensor: str):
        _powersensor = f'sensor.{powersensor}' if not powersensor.startswith('sensor.') else powersensor
        val_state = hass.states.get(_powersensor)
        if val_state is None:
            _LOGGER.error(f'Could not validate chosen powersensor {_powersensor}. It returned None as state.')
            raise FaultyPowerSensor
        elif not isinstance(float(val_state.state), float):
            _LOGGER.error(
                f'Could not validate chosen powersensor {_powersensor}. The value of its state is not a number. {val_state.state}'
            )
            raise FaultyPowerSensor

    @staticmethod
    async def validate_price_sensor(hass: HomeAssistant, pricesensor:str):
        _pricesensor = f'sensor.{pricesensor}' if not pricesensor.startswith('sensor.') else pricesensor
        val_state = hass.states.get(_pricesensor)
        if val_state is None:
            raise FaultyPowerSensor('It returned None as state.')

        if not isinstance(float(val_state.state), float):
            raise FaultyPriceSensor(f'Value of state is not a number. {val_state.state}')

        try:
            ConfigFlowValidation.validate_price_sensor_attributes(val_state.attributes)
        except Exception as e:
            raise FaultyPriceSensor(f'Could not validate chosen pricing sensor. {e}')

    @staticmethod
    def validate_price_sensor_attributes(attributes: dict):
        if 'today' not in attributes:
            raise ValueError('Today values is missing')
        if 'tomorrow_valid' not in attributes:
            raise ValueError('Tomorrow valid is missing.')
        if 'currency' not in attributes:
            raise ValueError('Currency is missing.')

    @staticmethod
    async def validate_input_first(data: dict) -> dict[str, Any]:
        if len(data['name']) < 3:
            raise ValueError
        if not data['name'].startswith('sensor.'):
            data['name'] = f"sensor.{data['name']}"
        return {'title': data['name']}

    @staticmethod
    async def validate_input_first_chargerid(data: dict) -> dict[str, Any]:
        """Validate the chargerId"""
        # if len(data["chargerid"]) < 1:
        #    raise ValueError

        return {'title': data['name']}


class FaultyPowerSensor(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class FaultyPriceSensor(exceptions.HomeAssistantError):
    def __init__(self, message=None):
        base_message = 'Could not validate chosen pricing sensor.'
        if message:
            base_message += ' ' + message
        super().__init__(base_message)

class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

"""Tests for config_flow: validation, schemas, helpers."""
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from custom_components.peaqev.config_flow import OptionsFlowHandler
from custom_components.peaqev.configflow.config_flow_helpers import \
    async_set_startpeak_dict
from custom_components.peaqev.configflow.config_flow_schemas import (
    CHARGER_DETAILS_SCHEMA, CHARGER_SCHEMA, HOURS_SCHEMA, MONTHS_SCHEMA,
    OUTLET_DETAILS_SCHEMA, PRICEAWARE_HOURS_SCHEMA, PRICEAWARE_SCHEMA, SCHEMAS,
    SENSOR_SCHEMA, TYPE_SCHEMA)
from custom_components.peaqev.configflow.config_flow_validation import (
    ConfigFlowValidation, FaultyPowerSensor, FaultyPriceSensor, InvalidHost)

# --- Schema Tests ---

@pytest.mark.asyncio
async def test_schemas_all_defined():
    """Test all expected schemas are defined."""
    assert TYPE_SCHEMA is not None
    assert SENSOR_SCHEMA is not None
    assert CHARGER_SCHEMA is not None
    assert CHARGER_DETAILS_SCHEMA is not None
    assert OUTLET_DETAILS_SCHEMA is not None
    assert HOURS_SCHEMA is not None
    assert PRICEAWARE_HOURS_SCHEMA is not None
    assert PRICEAWARE_SCHEMA is not None
    assert MONTHS_SCHEMA is not None


@pytest.mark.asyncio
async def test_schemas_list_contains_all():
    """Test SCHEMAS list contains all individual schemas."""
    assert len(SCHEMAS) >= 8
    assert TYPE_SCHEMA in SCHEMAS
    assert SENSOR_SCHEMA in SCHEMAS
    assert CHARGER_SCHEMA in SCHEMAS


# --- ConfigFlowValidation Tests ---

@pytest.mark.asyncio
async def test_validate_input_first_valid():
    """Test validate_input_first with valid name."""
    result = await ConfigFlowValidation.validate_input_first({'name': 'My EV Charger'})
    assert 'title' in result


@pytest.mark.asyncio
async def test_validate_input_first_adds_sensor_prefix():
    """Test validate_input_first adds 'sensor.' prefix."""
    result = await ConfigFlowValidation.validate_input_first({'name': 'test'})
    assert result['title'] == 'sensor.test'


@pytest.mark.asyncio
async def test_validate_input_first_empty_name():
    """Test validate_input_first with empty name."""
    with pytest.raises(Exception):
        await ConfigFlowValidation.validate_input_first({'name': ''})


@pytest.mark.asyncio
async def test_validate_input_first_chargerid_valid():
    """Test validate_input_first_chargerid with valid ID."""
    result = await ConfigFlowValidation.validate_input_first_chargerid({'chargerid': 'easee_001', 'name': 'test'})
    assert 'title' in result


@pytest.mark.asyncio
async def test_validate_input_first_chargerid_empty():
    """Test validate_input_first_chargerid with empty ID."""
    result = await ConfigFlowValidation.validate_input_first_chargerid({'chargerid': '', 'name': 'test'})
    assert 'title' in result


# --- Mock HA State Tests ---

class MockState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class MockStates:
    def __init__(self, data=None):
        self._data = data or {}

    def get(self, entity_id):
        return self._data.get(entity_id)


@pytest.mark.asyncio
async def test_validate_power_sensor_valid():
    """Test validate_power_sensor with valid numeric state."""
    mock_hass = type('MockHass', (), {'states': MockStates({'sensor.power': MockState('100.5')})})()
    await ConfigFlowValidation.validate_power_sensor(mock_hass, 'sensor.power')


@pytest.mark.asyncio
async def test_validate_power_sensor_invalid():
    """Test validate_power_sensor with non-numeric state."""
    mock_hass = type('MockHass', (), {'states': MockStates({'sensor.power': MockState('invalid')})})()
    with pytest.raises(Exception):
        await ConfigFlowValidation.validate_power_sensor(mock_hass, 'sensor.power')


@pytest.mark.asyncio
async def test_validate_power_sensor_missing():
    """Test validate_power_sensor with missing sensor."""
    mock_hass = type('MockHass', (), {'states': MockStates({})})()
    with pytest.raises(Exception):
        await ConfigFlowValidation.validate_power_sensor(mock_hass, 'sensor.power')


@pytest.mark.asyncio
async def test_validate_price_sensor_valid():
    """Test validate_price_sensor with valid state and attributes."""
    state = MockState('1.5', {'today': 1.0, 'tomorrow_valid': True, 'currency': 'NOK'})
    mock_hass = type('MockHass', (), {'states': MockStates({'sensor.price': state})})()
    await ConfigFlowValidation.validate_price_sensor(mock_hass, 'sensor.price')


@pytest.mark.asyncio
async def test_validate_price_sensor_missing_attributes():
    """Test validate_price_sensor with missing attributes."""
    state = MockState('1.5', {})
    mock_hass = type('MockHass', (), {'states': MockStates({'sensor.price': state})})()
    with pytest.raises(Exception):
        await ConfigFlowValidation.validate_price_sensor(mock_hass, 'sensor.price')


@pytest.mark.asyncio
async def test_validate_price_sensor_non_numeric():
    """Test validate_price_sensor with non-numeric state."""
    state = MockState('not_a_number', {})
    mock_hass = type('MockHass', (), {'states': MockStates({'sensor.price': state})})()
    with pytest.raises(Exception):
        await ConfigFlowValidation.validate_price_sensor(mock_hass, 'sensor.price')


# --- Price Sensor Attributes Tests ---

@pytest.mark.asyncio
async def test_validate_price_sensor_attributes_valid():
    """Test validate_price_sensor_attributes with valid attributes."""
    attributes = {'today': 1.0, 'tomorrow_valid': True, 'currency': 'NOK'}
    ConfigFlowValidation.validate_price_sensor_attributes(attributes)


@pytest.mark.asyncio
async def test_validate_price_sensor_attributes_missing():
    """Test validate_price_sensor_attributes with missing attributes."""
    with pytest.raises(ValueError):
        ConfigFlowValidation.validate_price_sensor_attributes({})


# --- Helper Function Tests ---

@pytest.mark.asyncio
async def test_async_set_startpeak_dict_valid():
    """Test async_set_startpeak_dict with valid data."""
    result = await async_set_startpeak_dict({'jan': 100, 'feb': 200, 'mar': 300, 'apr': 400, 'may': 500, 'jun': 600, 'jul': 700, 'aug': 800, 'sep': 900, 'oct': 1000, 'nov': 1100, 'dec': 1200})
    assert result == {1: 100, 2: 200, 3: 300, 4: 400, 5: 500, 6: 600, 7: 700, 8: 800, 9: 900, 10: 1000, 11: 1100, 12: 1200}


@pytest.mark.asyncio
async def test_async_set_startpeak_dict_empty():
    """Test async_set_startpeak_dict with empty dict."""
    with pytest.raises(KeyError):
        await async_set_startpeak_dict({})


@pytest.mark.asyncio
async def test_async_set_startpeak_dict_string_keys():
    """Test async_set_startpeak_dict with month name keys."""
    result = await async_set_startpeak_dict({'jan': 150, 'feb': 250, 'mar': 350, 'apr': 450, 'may': 550, 'jun': 650, 'jul': 750, 'aug': 850, 'sep': 950, 'oct': 1050, 'nov': 1150, 'dec': 1250})
    assert all(isinstance(k, int) for k in result.keys())


# --- Error Classes Tests ---

@pytest.mark.asyncio
async def test_faulty_power_sensor_is_ha_error():
    """Test FaultyPowerSensor is a HomeAssistantError."""
    from homeassistant.exceptions import HomeAssistantError
    assert issubclass(FaultyPowerSensor, HomeAssistantError)


@pytest.mark.asyncio
async def test_faulty_price_sensor_is_ha_error():
    """Test FaultyPriceSensor is a HomeAssistantError."""
    from homeassistant.exceptions import HomeAssistantError
    assert issubclass(FaultyPriceSensor, HomeAssistantError)


@pytest.mark.asyncio
async def test_invalid_host_is_ha_error():
    """Test InvalidHost is a HomeAssistantError."""
    from homeassistant.exceptions import HomeAssistantError
    assert issubclass(InvalidHost, HomeAssistantError)


# --- OptionsFlowHandler Tests ---

@pytest.mark.asyncio
async def test_options_flow_carries_over_existing_options():
    """Options not touched by the steps of this run must survive it.

    config_entry isn't available in __init__, so the handler seeds itself on
    the first step instead. Without that, a run that skips a step drops the
    values that step owns back to the initial setup defaults.
    """
    entry = MagicMock()
    entry.options = {'nonhours': [1, 2, 3], 'priceaware': False}
    entry.data = {'nonhours': [23], 'name': 'sensor.setup_default'}

    handler = OptionsFlowHandler()
    assert handler.options == {}

    with patch.object(
        type(handler), 'config_entry', new_callable=PropertyMock, return_value=entry
    ):
        await handler.async_step_init()
        assert handler.options['nonhours'] == [1, 2, 3]

        # a later step only updates its own keys
        handler.options.update({'priceaware': True})
        assert handler.options['nonhours'] == [1, 2, 3]

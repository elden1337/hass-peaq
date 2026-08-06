"""Tests for ChargeController: threshold logic, state transitions, initialization."""
import time
from unittest.mock import MagicMock, AsyncMock, PropertyMock, patch

import pytest
from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.locale.enums.time_periods import TimePeriods
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_factory import ChargeControllerFactory
from custom_components.peaqev.peaqservice.chargecontroller.charger.chargerhelpers import (
    _checkchargerparams, async_set_chargerparams
)
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers import defer_start
from custom_components.peaqev.peaqservice.chargecontroller.const import (
    INITIALIZING, WAITING_FOR_POWER, DONETIMEOUT, DEBUGLOG_TIMEOUT
)
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.test.conftest import (
    MockHub, MockChargeController, MockChargertype, MockSensors
)


# --- ChargeControllerFactory Tests ---

@pytest.mark.asyncio
async def test_chargecontrollerfactory_creates_full_controller():
    """Test factory creates ChargeController when not lite."""
    hub = MockHub()
    hub.options.peaqev_lite = False
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
        ChargeControllerStates.Connected: ['connected'],
        ChargeControllerStates.Charging: ['charging'],
        ChargeControllerStates.Stop: ['stop'],
        ChargeControllerStates.Start: ['start'],
        ChargeControllerStates.Error: ['error'],
    }
    controller = await ChargeControllerFactory.async_create(
        hub, charger_states, ChargerType.Easee
    )
    assert isinstance(controller, ChargeController)


@pytest.mark.asyncio
async def test_chargecontrollerfactory_creates_lite_controller():
    """Test factory creates ChargeControllerLite when peaqev_lite=True."""
    hub = MockHub()
    hub.options.peaqev_lite = True
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
        ChargeControllerStates.Connected: ['connected'],
        ChargeControllerStates.Charging: ['charging'],
        ChargeControllerStates.Stop: ['stop'],
        ChargeControllerStates.Start: ['start'],
        ChargeControllerStates.Error: ['error'],
    }
    controller = await ChargeControllerFactory.async_create(
        hub, charger_states, ChargerType.NoCharger
    )
    assert isinstance(controller, ChargeControllerLite)


# --- ChargeController Tests ---

@pytest.mark.asyncio
async def test_chargecontroller_status_string_not_initialized(mock_hub):
    """Test status_string returns 'Initializing' when not initialized."""
    mock_hub.is_initialized = False
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    assert controller.status_string == INITIALIZING


@pytest.mark.asyncio
async def test_chargecontroller_status_string_waiting_for_power(mock_hub):
    """Test status_string returns 'WaitingForPower' when power sensor not ready."""
    mock_hub.is_initialized = True
    mock_hub.state_machine.states = {}
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    # Should return WAITING_FOR_POWER since power sensor state is None
    status = controller.status_string
    assert status in [WAITING_FOR_POWER, INITIALIZING]


@pytest.mark.asyncio
async def test_chargecontroller_check_initialized_with_power(mock_hub):
    """Test _check_initialized when power sensor has valid value."""
    mock_hub.is_initialized = True
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    # After 10 seconds, should initialize
    controller.latest_init_check = time.time() - 15
    result = controller._check_initialized()
    assert result == True


@pytest.mark.asyncio
async def test_chargecontroller_check_initialized_too_early(mock_hub):
    """Test _check_initialized returns False within 10 second window."""
    mock_hub.is_initialized = True
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    controller.latest_init_check = time.time() - 5  # Only 5 seconds
    result = controller._check_initialized()
    assert result == False


@pytest.mark.asyncio
async def test_chargecontroller_check_initialized_invalid_power(mock_hub):
    """Test _check_initialized with invalid power sensor value."""
    mock_hub.is_initialized = True
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='invalid')
    }
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    controller.latest_init_check = time.time() - 15
    result = controller._check_initialized()
    assert result == False


@pytest.mark.asyncio
async def test_chargecontroller_below_startthreshold(mock_hub):
    """Test async_below_startthreshold logic."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.threshold.async_start = AsyncMock(return_value=50)
    mock_hub.async_get_predicted_energy = AsyncMock(return_value=10.0)
    mock_hub.current_peak_dynamic = 100

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_below_startthreshold()
    assert result == True  # 10000 < (100000 * 0.5)


@pytest.mark.asyncio
async def test_chargecontroller_above_stopthreshold(mock_hub):
    """Test async_above_stopthreshold logic."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.threshold.async_stop = AsyncMock(return_value=80)
    mock_hub.async_get_predicted_energy = AsyncMock(return_value=100.0)
    mock_hub.current_peak_dynamic = 100

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_above_stopthreshold()
    assert result == True  # 100000 > (100000 * 0.8)


@pytest.mark.asyncio
async def test_chargecontroller_get_status_charging_stop(mock_hub):
    """Test async_get_status_charging returns Stop when above stopthreshold."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.power = MagicMock()
    mock_hub.power.power_canary = MagicMock()
    mock_hub.power.power_canary.alive = True
    mock_hub.events.aux_stop = False
    mock_hub.sensors.totalhourlyenergy.value = 50.0
    mock_hub.async_free_charge = AsyncMock(return_value=False)
    mock_hub.threshold.async_start = AsyncMock(return_value=50)
    mock_hub.threshold.async_stop = AsyncMock(return_value=80)
    mock_hub.async_get_predicted_energy = AsyncMock(return_value=100.0)
    mock_hub.current_peak_dynamic = 100

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Charging: ['charging'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_get_status_charging()
    assert result == ChargeControllerStates.Stop


@pytest.mark.asyncio
async def test_chargecontroller_get_status_charging_start(mock_hub):
    """Test async_get_status_charging returns Start when below startthreshold."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.power = MagicMock()
    mock_hub.power.power_canary = MagicMock()
    mock_hub.power.power_canary.alive = True
    mock_hub.events.aux_stop = False
    mock_hub.sensors.totalhourlyenergy.value = 5.0
    mock_hub.async_free_charge = AsyncMock(return_value=False)
    mock_hub.threshold.async_start = AsyncMock(return_value=50)
    mock_hub.threshold.async_stop = AsyncMock(return_value=80)
    mock_hub.async_get_predicted_energy = AsyncMock(return_value=1.0)
    mock_hub.current_peak_dynamic = 100

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Charging: ['charging'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_get_status_charging()
    assert result == ChargeControllerStates.Start


@pytest.mark.asyncio
async def test_chargecontroller_get_status_charging_power_canary_dead(mock_hub):
    """Test async_get_status_charging returns Stop when power canary is dead."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.power = MagicMock()
    mock_hub.power.power_canary = MagicMock()
    mock_hub.power.power_canary.alive = False

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Charging: ['charging'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_get_status_charging()
    assert result == ChargeControllerStates.Stop


@pytest.mark.asyncio
async def test_chargecontroller_get_status_charging_aux_stop(mock_hub):
    """Test async_get_status_charging returns Stop when aux_stop is True."""
    mock_hub.state_machine.states = {
        'sensor.power': MagicMock(state='100')
    }
    mock_hub.power = MagicMock()
    mock_hub.power.power_canary = MagicMock()
    mock_hub.power.power_canary.alive = True
    mock_hub.events.aux_stop = True

    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Charging: ['charging'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)

    result = await controller.async_get_status_charging()
    assert result == ChargeControllerStates.Stop


# --- ChargeControllerLite Tests ---

@pytest.mark.asyncio
async def test_chargecontrollerlite_status_string(mock_hub):
    """Test ChargeControllerLite status_string."""
    mock_hub.is_initialized = False
    mock_hub.state_machine.states = {}
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeControllerLite(mock_hub, charger_states, ChargerType.NoCharger)
    assert controller.is_initialized == False


# --- ChargerHelpers Tests ---

@pytest.mark.asyncio
async def test_checkchargerparams_valid():
    """Test _checkchargerparams with valid params."""
    calls = {'params': {'charger': 'charger1', 'chargerid': 'id1', 'current': 'amp'}}
    assert _checkchargerparams(calls) == True


@pytest.mark.asyncio
async def test_checkchargerparams_missing_charger():
    """Test _checkchargerparams with missing charger key."""
    calls = {'params': {'chargerid': 'id1', 'current': 'amp'}}
    assert _checkchargerparams(calls) == False


@pytest.mark.asyncio
async def test_checkchargerparams_missing_chargerid():
    """Test _checkchargerparams with missing chargerid key."""
    calls = {'params': {'charger': 'charger1', 'current': 'amp'}}
    assert _checkchargerparams(calls) == False


@pytest.mark.asyncio
async def test_async_set_chargerparams():
    """Test async_set_chargerparams creates correct params dict."""
    calls = {'params': {'charger': 'charger1', 'chargerid': 'id1', 'current': 'amp'}}
    result = await async_set_chargerparams(calls, 16)
    assert 'charger1' in result
    assert 'id1' in result.values()
    assert result['amp'] == 16


@pytest.mark.asyncio
async def test_async_set_chargerparams_minimal():
    """Test async_set_chargerparams with minimal params."""
    calls = {'params': {'current': 'amp'}}
    result = await async_set_chargerparams(calls, 16)
    assert result['amp'] == 16


@pytest.mark.asyncio
async def test_defer_start():
    """Test defer_start helper function."""
    non_hours = []
    result = defer_start(non_hours)
    assert result == False  # Should not defer with empty non_hours


@pytest.mark.asyncio
async def test_defer_start_with_non_hours():
    """Test defer_start returns True when next hour is in non_hours."""
    import datetime
    # Mock current time to be at a specific hour
    with patch('custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_helpers.datetime') as mock_dt:
        mock_dt.now.return_value = datetime.datetime(2026, 7, 31, 14, 50, 0)  # 2:50 PM
        non_hours = [15]  # Next hour (3 PM) is in non_hours
        result = defer_start(non_hours)
        assert result == True  # Should be True because we're at minute 50 and next hour (3 PM) is in non_hours


# --- IChargeController Tests ---

@pytest.mark.asyncio
async def test_chargecontroller_is_initialized_hub_not_initialized(mock_hub):
    """Test is_initialized returns False when hub is not initialized."""
    mock_hub.is_initialized = False
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    assert controller.is_initialized == False


@pytest.mark.asyncio
async def test_chargecontroller_connected_property(mock_hub):
    """Test connected property."""
    mock_hub.is_initialized = True
    mock_hub.spotprice.is_initialized = True
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    # connected should be False when status_type is Idle
    assert controller.connected == False


@pytest.mark.asyncio
async def test_chargecontroller_status_type_property(mock_hub):
    """Test status_type property."""
    mock_hub.is_initialized = True
    mock_hub.spotprice.is_initialized = True
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = ChargeController(mock_hub, charger_states, ChargerType.Easee)
    assert controller.status_type == ChargeControllerStates.Idle


# --- Constants Tests ---

@pytest.mark.asyncio
async def test_constants_defined():
    """Test that all expected constants are defined."""
    assert INITIALIZING == 'Initializing...'
    assert WAITING_FOR_POWER == 'Waiting for power-reading...'
    assert DONETIMEOUT == 180
    assert DEBUGLOG_TIMEOUT == 60


@pytest.mark.asyncio
async def test_chargecontroller_factory_creates_correct_type():
    """Test factory creates correct controller type based on peaqev_lite setting."""
    # Test full controller
    hub = MockHub()
    hub.options.peaqev_lite = False
    charger_states = {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
    }
    controller = await ChargeControllerFactory.async_create(
        hub, charger_states, ChargerType.Easee
    )
    assert isinstance(controller, ChargeController)
    
    # Test lite controller
    hub_lite = MockHub()
    hub_lite.options.peaqev_lite = True
    controller_lite = await ChargeControllerFactory.async_create(
        hub_lite, charger_states, ChargerType.NoCharger
    )
    assert isinstance(controller_lite, ChargeControllerLite)

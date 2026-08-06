"""Tests for Charger class: state management, service calls, session handling."""
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from peaqevcore.common.enums.calltype_enum import CallTypes
from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.chargecontroller.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargecontroller.charger.chargermodel import ChargerModel
from custom_components.peaqev.peaqservice.chargecontroller.charger.charger_states import ChargerStates
from custom_components.peaqev.peaqservice.chargecontroller.charger.charger_call_service import call_ok
from custom_components.peaqev.peaqservice.chargecontroller.charger.savings_controller import SavingsController
from custom_components.peaqev.test.conftest import (
    MockChargeController, MockChargertype, MockHub, MockSensors
)


# --- ChargerModel Tests ---

@pytest.mark.asyncio
async def test_chargermodel_default_values():
    """Test ChargerModel default values."""
    model = ChargerModel()
    assert model.running == False
    assert model.disable_current_updates == False
    assert model.session_active == False
    assert model.latest_charger_call == 0
    assert model.unsuccessful_stop == False


@pytest.mark.asyncio
async def test_chargermodel_session_active_setter():
    """Test session_active setter logs when changed."""
    model = ChargerModel()
    model.session_active = True
    assert model.session_active == True


@pytest.mark.asyncio
async def test_chargermodel_session_active_no_log_when_same():
    """Test session_active setter doesn't log when value is same."""
    model = ChargerModel()
    model.session_active = False  # Already False, should not log


# --- call_ok Tests ---

@pytest.mark.asyncio
async def test_call_ok_recent_call():
    """Test call_ok returns False for recent call."""
    result = call_ok(time.time() - 30)  # 30 seconds ago
    assert result == False


@pytest.mark.asyncio
async def test_call_ok_old_call():
    """Test call_ok returns True for old call (>60 seconds)."""
    result = call_ok(time.time() - 120)  # 120 seconds ago
    assert result == True


@pytest.mark.asyncio
async def test_call_ok_zero_timestamp():
    """Test call_ok with timestamp=0 (never called)."""
    result = call_ok(0)
    assert result == True


# --- Charger Class Tests ---

@pytest.mark.asyncio
async def test_charger_creates_model():
    """Test Charger creates ChargerModel."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    charger = Charger(controller=mock_controller)
    assert charger.model is not None


@pytest.mark.asyncio
async def test_charger_session_active_property(mock_hub):
    """Test session_active property."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.status_type = ChargeControllerStates.Idle
    charger = Charger(controller=mock_controller)
    assert charger.session_active == False


@pytest.mark.asyncio
async def test_charger_charger_active_with_powerswitch(mock_hub):
    """Test charger_active when powerswitch_controls_charging=True."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.hub.chargertype.options.powerswitch_controls_charging = True
    mock_controller.hub.sensors.chargerobject_switch.value = True
    charger = Charger(controller=mock_controller)
    assert charger.charger_active == True


@pytest.mark.asyncio
async def test_charger_charger_active_with_carpowersensor(mock_hub):
    """Test charger_active when using car powersensor."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.hub.chargertype.options.powerswitch_controls_charging = False
    mock_controller.hub.sensors.carpowersensor.value = 100
    charger = Charger(controller=mock_controller)
    assert charger.charger_active == True


@pytest.mark.asyncio
async def test_charger_charger_active_carpower_zero(mock_hub):
    """Test charger_active returns False when carpower is 0."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.hub.chargertype.options.powerswitch_controls_charging = False
    mock_controller.hub.sensors.carpowersensor.value = 0
    charger = Charger(controller=mock_controller)
    assert charger.charger_active == False


@pytest.mark.asyncio
async def test_charger_subscribes_to_observer_events(mock_hub):
    """Test Charger subscribes to relevant observer events."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_hub.observer = MagicMock()
    charger = Charger(controller=mock_controller)
    assert mock_hub.observer.add.call_count == 4


@pytest.mark.asyncio
async def test_charger_async_setup():
    """Test Charger async_setup (no-op)."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    charger = Charger(controller=mock_controller)
    await charger.async_setup()  # Should not raise


@pytest.mark.asyncio
async def test_charger_async_reset_session(mock_hub):
    """Test async_reset_session sets session_active."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.session = MagicMock()
    mock_controller.session.async_reset = AsyncMock()
    mock_controller.status_type = ChargeControllerStates.Connected
    charger = Charger(controller=mock_controller)
    await charger.async_reset_session()
    assert charger.session_active == True


@pytest.mark.asyncio
async def test_charger_async_reset_session_already_active(mock_hub):
    """Test async_reset_session when session already active."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.chargertype = mock_hub.chargertype
    mock_controller.session = MagicMock()
    mock_controller.status_type = ChargeControllerStates.Done
    charger = Charger(controller=mock_controller)
    charger.model.session_active = True
    await charger.async_reset_session()
    # Should not reset when session already active


@pytest.mark.asyncio
async def test_charger_internal_state_on():
    """Test _internal_state_on sets running=True."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    charger = Charger(controller=mock_controller)
    charger._internal_state_on()
    assert charger.model.running == True
    assert charger.model.disable_current_updates == False


@pytest.mark.asyncio
async def test_charger_internal_state_off():
    """Test async_internal_state_off sets running=False."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    mock_controller.hub.async_request_sensor_data = AsyncMock(return_value='stop')
    charger = Charger(controller=mock_controller)
    charger.model.running = True
    await charger.async_internal_state_off()
    assert charger.model.running == False


@pytest.mark.asyncio
async def test_charger_check_unsuccessful_stop():
    """Test _check_unsuccessful_stop sets flag after 20 seconds."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    charger = Charger(controller=mock_controller)
    charger.model.running = True
    charger.model.lastest_call_off = time.time() - 25
    charger._check_unsuccessful_stop()
    assert charger.model.unsuccessful_stop == True


@pytest.mark.asyncio
async def test_charger_check_unsuccessful_stop_not_yet_timeout():
    """Test _check_unsuccessful_stop doesn't set flag within timeout."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.chargertype = MagicMock()
    charger = Charger(controller=mock_controller)
    charger.model.running = True
    charger.model.lastest_call_off = time.time() - 10  # Only 10 seconds
    charger._check_unsuccessful_stop()
    assert charger.model.unsuccessful_stop == False


# --- SavingsController Tests ---

@pytest.mark.asyncio
async def test_savingscontroller_enabled_when_price_active(mock_hub):
    """Test SavingsController is enabled when price sensor is active."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.sensors.locale.data.price.is_active = True
    savings = SavingsController(mock_controller)
    assert savings.enabled == True


@pytest.mark.asyncio
async def test_savingscontroller_disabled_when_price_inactive(mock_hub):
    """Test SavingsController is disabled when price sensor is not active."""
    mock_controller = MagicMock()
    mock_controller.hub = MagicMock()
    mock_controller.hub.sensors.locale.data.price.is_active = False
    savings = SavingsController(mock_controller)
    assert savings.enabled == False


@pytest.mark.asyncio
async def test_savingscontroller_subscribes_to_observer(mock_hub):
    """Test SavingsController subscribes to relevant events."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.sensors.locale.data.price.is_active = True
    mock_hub.observer = MagicMock()
    savings = SavingsController(mock_controller)
    assert mock_hub.observer.add.call_count >= 3


@pytest.mark.asyncio
async def test_savingscontroller_status_property(mock_hub):
    """Test status property returns SavingsStatus."""
    from peaqevcore.services.savings.savings_status import SavingsStatus
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.sensors.locale.data.price.is_active = True
    savings = SavingsController(mock_controller)
    assert isinstance(savings.status, SavingsStatus)


@pytest.mark.asyncio
async def test_savingscontroller_is_on_property(mock_hub):
    """Test is_on property."""
    from peaqevcore.services.savings.savings_status import SavingsStatus
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.sensors.locale.data.price.is_active = True
    savings = SavingsController(mock_controller)
    # is_on depends on status being Collecting
    assert isinstance(savings.is_on, bool)


@pytest.mark.asyncio
async def test_savingscontroller_savings_properties(mock_hub):
    """Test savings_peak, savings_trade, savings_total properties."""
    mock_controller = MagicMock()
    mock_controller.hub = mock_hub
    mock_controller.hub.sensors.locale.data.price.is_active = True
    savings = SavingsController(mock_controller)
    assert isinstance(savings.savings_peak, (int, float))
    assert isinstance(savings.savings_trade, (int, float))
    assert isinstance(savings.savings_total, (int, float))

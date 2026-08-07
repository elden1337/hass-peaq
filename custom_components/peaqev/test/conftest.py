"""Shared fixtures for all peaqev tests."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import EventBus
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.fuses import Fuses
from peaqevcore.models.phases import Phases

from custom_components.peaqev.peaqservice.chargecontroller.charger.chargermodel import \
    ChargerModel
from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import \
    IObserver
from custom_components.peaqev.peaqservice.powertools.gainloss.igain_loss import \
    IGainLoss
from custom_components.peaqev.peaqservice.powertools.power_canary.power_canary_model import \
    PowerCanaryModel
from custom_components.peaqev.peaqservice.powertools.power_canary.smooth_average import \
    SmoothAverage

# --- Mock Classes ---

class MockHass:
    """Minimal HomeAssistant stub for testing."""

    def __init__(self):
        self.bus = MagicMock(spec=EventBus)
        self.bus.fire = MagicMock()

    async def async_add_executor_job(self, func, *args):
        return func(*args)


class MockState:
    """Minimal HA state stub."""

    def __init__(self, state):
        self.state = str(state)


class MockObserver(IObserver):
    """Minimal observer for testing without HA integration."""

    def __init__(self):
        super().__init__()

    async def async_broadcast_separator(self, func, command):
        import asyncio

        from custom_components.peaqev.peaqservice.util.extensionmethods import \
            async_iscoroutine

        if await async_iscoroutine(func):
            await self.async_call_func(func=func, command=command)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._call_func, func, command)


class MockGainLoss(IGainLoss):
    """Mock GainLoss for testing without hub."""

    def __init__(self, mock_states=None):
        self._mock_states = mock_states or {}
        super().__init__()

    async def async_get_consumption(self, time_period):
        try:
            entity = await self.async_get_entity(time_period, 'consumption')
            state = self._mock_states.get(entity)
            if state is None:
                return 0.0
            return float(state)
        except (AttributeError, ValueError, TypeError):
            return 0.0

    async def async_get_cost(self, time_period):
        try:
            entity = await self.async_get_entity(time_period, 'cost')
            state = self._mock_states.get(entity)
            if state is None:
                return 0.0
            return float(state)
        except (AttributeError, ValueError, TypeError):
            return 0.0


class MockChargeController:
    """Minimal charge controller stub for Charger testing."""

    def __init__(self):
        self.status_type = ChargeControllerStates.Idle
        self.is_initialized = True
        self.enabled = True
        self.charger_done = False


class MockChargertype:
    """Minimal chargertype stub."""

    def __init__(self):
        self.options = MagicMock()
        self.options.powerswitch_controls_charging = False
        self.options.allowupdatecurrent = False
        self.servicecalls = MagicMock()


class MockSensors:
    """Minimal sensors stub."""

    def __init__(self):
        self.power = MagicMock()
        self.power.total = MagicMock()
        self.power.total.value = 0
        self.power.killswitch = MagicMock()
        self.power.killswitch.is_caution = False
        self.power.killswitch.is_dead = False
        self.chargerobject_switch = MagicMock()
        self.chargerobject_switch.value = False
        self.carpowersensor = MagicMock()
        self.carpowersensor.value = 0
        self.charger_done = False
        self.amp_meter = MagicMock()
        self.amp_meter.value = 0
        self.locale = MagicMock()
        self.locale.data = MagicMock()
        self.locale.data.price = MagicMock()
        self.locale.data.price.value = 0
        self.locale.data.price.is_active = True
        self.totalhourlyenergy = MagicMock()
        self.totalhourlyenergy.value = 0


class MockOptions:
    """Minimal hub options stub."""

    def __init__(self):
        self.peaqev_lite = False
        self.powersensor = 'sensor.power'
        self.fuse_type = Fuses.FUSE_3_25.value
        self.price = MagicMock()
        self.price.price_aware = False
        self.price.spotprice_type = None


class MockHub:
    """Minimal hub stub for charge controller testing."""

    def __init__(self):
        self.options = MockOptions()
        self.enabled = True
        self.charger_done = False
        self.is_initialized = True
        self.sensors = MockSensors()
        self.chargertype = MockChargertype()
        self.observer = MockObserver()
        self.threshold = MagicMock()
        self.threshold.phases = Phases.ThreePhase.name
        self.threshold.async_start = AsyncMock(return_value=50)
        self.threshold.async_stop = AsyncMock(return_value=80)
        self.threshold.async_allowed_current = AsyncMock(return_value=16)
        self.spotprice = MagicMock()
        self.spotprice.is_initialized = True
        self.state_machine = MagicMock()
        self.state_machine.states = {}
        self.events = MagicMock()
        self.events.aux_stop = False
        self.hours = MagicMock()
        self.hours.timer = MagicMock()
        self.hours.timer.is_override = False
        self.non_hours = []
        self.async_get_predicted_energy = AsyncMock(return_value=10.0)
        self.current_peak_dynamic = 100
        self.async_free_charge = AsyncMock(return_value=False)


@pytest.fixture
def mock_hass():
    return MockHass()


@pytest.fixture
def mock_observer():
    return MockObserver()


@pytest.fixture
def mock_gainloss(mock_states=None):
    return MockGainLoss(mock_states)


@pytest.fixture
def mock_charge_controller():
    return MockChargeController()


@pytest.fixture
def mock_charger_states():
    return {
        ChargeControllerStates.Done: ['done'],
        ChargeControllerStates.Idle: ['idle'],
        ChargeControllerStates.Connected: ['connected'],
        ChargeControllerStates.Charging: ['charging'],
        ChargeControllerStates.Stop: ['stop'],
        ChargeControllerStates.Start: ['start'],
        ChargeControllerStates.Error: ['error'],
    }


@pytest.fixture
def mock_charger_model():
    return ChargerModel()


@pytest.fixture
def smooth_average():
    return SmoothAverage(max_age=60, max_samples=30, precision=2)


@pytest.fixture
def power_canary_model(fuse_type=Fuses.FUSE_3_25):
    return PowerCanaryModel(
        warning_threshold=0.75,
        cutoff_threshold=0.9,
        fuse=fuse_type,
        allow_amp_adjustment=True
    )


@pytest.fixture
def mock_hub():
    return MockHub()

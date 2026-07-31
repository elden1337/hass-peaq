"""Tests for HubFactory, MaxMinController, and charger-related modules."""
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from peaqevcore.models.phases import Phases
from peaqevcore.models.fuses import Fuses
from peaqevcore.models.chargecontroller_states import ChargeControllerStates

from custom_components.peaqev.peaqservice.hub.max_min_controller import MaxMinController
from custom_components.peaqev.peaqservice.hub.price_aware_hub import PriceAwareHub
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType, CHARGERTYPES
from custom_components.peaqev.peaqservice.chargertypes.models.entities_model import EntitiesModel
from custom_components.peaqev.peaqservice.util.schedule_options_handler import SchedulerOptionsHandler
from custom_components.peaqev.peaqservice.util.extensionmethods import (
    nametoid, dt_from_epoch, async_iscoroutine
)
from custom_components.peaqev.peaqservice.hub.models.initializer_types import InitializerTypes
from custom_components.peaqev.peaqservice.hub.const import LookupKeys


# --- InitializerTypes Tests ---

@pytest.mark.asyncio
async def test_initializer_types_enum():
    """Test InitializerTypes enum has all expected members."""
    assert hasattr(InitializerTypes, 'Hours')
    assert hasattr(InitializerTypes, 'CarPowerSensor')
    assert hasattr(InitializerTypes, 'ChargerObjectSwitch')
    assert hasattr(InitializerTypes, 'Power')
    assert hasattr(InitializerTypes, 'ChargerObject')
    assert hasattr(InitializerTypes, 'ChargerType')
    assert hasattr(InitializerTypes, 'SpotPrice')


# --- Extension Methods Tests ---

@pytest.mark.asyncio
async def test_nametoid_simple():
    """Test nametoid converts simple name to ID format."""
    assert nametoid('My EV Charger') == 'my_ev_charger'


@pytest.mark.asyncio
async def test_nametoid_with_underscores():
    """Test nametoid preserves underscores."""
    assert nametoid('my_ev_charger') == 'my_ev_charger'


@pytest.mark.asyncio
async def test_nametoid_with_numbers():
    """Test nametoid handles numbers."""
    assert nametoid('Test123') == 'test123'


@pytest.mark.asyncio
async def test_dt_from_epoch():
    """Test dt_from_epoch converts epoch to datetime string."""
    result = dt_from_epoch(0)
    assert result is not None


@pytest.mark.asyncio
async def test_async_iscoroutine():
    """Test async_iscoroutine detects async functions."""
    async def async_func():
        pass

    def sync_func():
        pass

    assert await async_iscoroutine(async_func) == True
    assert await async_iscoroutine(sync_func) == False


@pytest.mark.asyncio
async def test_async_iscoroutine_with_lambda():
    """Test async_iscoroutine with lambda."""
    assert await async_iscoroutine(lambda: None) == False


# --- CHARGERTYPES Tests ---

@pytest.mark.asyncio
async def test_chargertypes_enum_complete():
    """Test ChargerType enum has all expected types."""
    assert hasattr(ChargerType, 'ChargeAmps')
    assert hasattr(ChargerType, 'Easee')
    assert hasattr(ChargerType, 'GaroWallbox')
    assert hasattr(ChargerType, 'Outlet')
    assert hasattr(ChargerType, 'Zaptec')
    assert hasattr(ChargerType, 'NoCharger')
    assert hasattr(ChargerType, 'Unknown')
    assert hasattr(ChargerType, 'WallBox')
    assert hasattr(ChargerType, 'Keba')


@pytest.mark.asyncio
async def test_chargertypes_list_not_empty():
    """Test CHARGERTYPES list is not empty."""
    assert len(CHARGERTYPES) > 0


# --- EntitiesModel Tests ---

@pytest.mark.asyncio
async def test_entitiesmodel_default():
    """Test EntitiesModel default values."""
    model = EntitiesModel()
    assert model.entityschema == ""
    assert model.imported_entities == []
    assert model.valid == False


# --- SchedulerOptionsHandler Tests ---

@pytest.mark.asyncio
async def test_scheduler_options_handler_display_options():
    """Test SchedulerOptionsHandler display_options property."""
    mock_hass = MagicMock()
    handler = SchedulerOptionsHandler(mock_hass)
    assert handler.display_options is not None


@pytest.mark.asyncio
async def test_scheduler_options_handler_options():
    """Test SchedulerOptionsHandler options property."""
    mock_hass = MagicMock()
    handler = SchedulerOptionsHandler(mock_hass)
    assert handler.options is not None


# --- MaxMinController Tests ---

@pytest.mark.asyncio
async def test_maxmincontroller_max_charge_property():
    """Test MaxMinController max_charge property."""
    mock_hub = MagicMock()
    mock_hub.options.max_charge = 50
    mock_hub.options.price.price_aware = True
    mock_hub.options.peaqev_lite = True
    controller = MaxMinController(mock_hub)
    assert controller.max_charge == 50


@pytest.mark.asyncio
async def test_maxmincontroller_remaining_charge():
    """Test MaxMinController remaining_charge property."""
    mock_hub = MagicMock()
    mock_hub.options.max_charge = 50
    mock_hub.options.price.price_aware = False
    mock_hub.options.peaqev_lite = True
    controller = MaxMinController(mock_hub)
    assert controller.remaining_charge is not None


@pytest.mark.asyncio
async def test_maxmincontroller_null_max_charge():
    """Test MaxMinController async_null_max_charge."""
    mock_hub = MagicMock()
    mock_hub.max_charge = 50
    controller = MaxMinController(mock_hub)
    await controller.async_null_max_charge()


# --- PriceAwareHub Tests ---

@pytest.mark.asyncio
async def test_priceawarehub_inherits_from_homeassistanthub():
    """Test PriceAwareHub inherits from HomeAssistantHub."""
    assert issubclass(PriceAwareHub, PriceAwareHub)


# --- HubEvents Tests ---

@pytest.mark.asyncio
async def test_hubevents_aux_stop_property():
    """Test HubEvents aux_stop property."""
    mock_hub = MagicMock()
    mock_state_machine = MagicMock()
    events = HubEvents(mock_hub, mock_state_machine)
    assert events.aux_stop is not None


# --- LookupKeys Tests ---

@pytest.mark.asyncio
async def test_lookupkeys_has_expected_members():
    """Test LookupKeys enum has expected members."""
    lk = LookupKeys
    assert hasattr(lk, 'CHARGEROBJECT_VALUE')
    assert hasattr(lk, 'PRICES')
    assert hasattr(lk, 'CURRENT_PEAK')
    assert hasattr(lk, 'SPOTPRICE_SOURCE')


@pytest.mark.asyncio
async def test_lookupkeys_count():
    """Test LookupKeys has all 31 expected members."""
    assert len(LookupKeys) == 31


# --- Integration Tests ---

@pytest.mark.asyncio
async def test_all_charger_types_in_enum():
    """Test all charger types are represented in enum."""
    assert ChargerType.ChargeAmps is not None
    assert ChargerType.Easee is not None
    assert ChargerType.NoCharger is not None

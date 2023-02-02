from peaqevcore.hub.hub_options import HubOptions
import pytest
from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData

import copy
import datetime

#from freezegun import freeze_time
from homeassistant.components import sensor
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.restore_state import (
    DATA_RESTORE_STATE_TASK,
    RestoreStateData,
    StoredState,
)
from homeassistant.setup import async_setup_component
from homeassistant.util import dt
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockEntity, mock_integration, MockModule, mock_entity_platform, MockPlatform, mock_registry
from custom_components.peaqev.__init__ import async_setup_entry
from peaqevcore.services.locale.Locale import LOCALES
from peaqevcore.models.hourselection.cautionhourtype import CautionHourType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import Charger_type
from custom_components.peaqev.peaqservice.util.constants import CAUTIONHOURTYPE_NAMES, INSTALLATIONTYPES
from unittest.mock import AsyncMock
from homeassistant import config_entries


DOMAIN = "peaqev"
MOCK_CONFIG = {
"locale": "Göteborg, Sweden",
"chargertype": Charger_type.ChargeAmps.value,
"chargerid": "test123",
"startpeaks": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 1, "9": 1, "10": 1, "11": 1, "12": 1},
"cautionhour_type": "suave",
"name": "sensor.power_meter"
}
CHARGEAMPS_CONFIG = {
    "sensor": {
        "platform": "chargeamps",
        "name": "123456M 1 power"
    }
}

@pytest.fixture
def manager(hass):
    """Fixture of a loaded config manager."""
    manager = config_entries.ConfigEntries(hass, {})
    hass.config_entries = manager
    return manager

@pytest.mark.asyncio
async def test1(hass):

    
    async def mock_setup_entry_platform(hass, entry, async_add_entities):
        """Mock setting up platform."""
        async_add_entities([entity])

    platform = MockPlatform(
        async_setup_entry=async_setup_entry
    )
    config_entry = MockConfigEntry(domain="magnus", entry_id="test1")
    entity_platform = mock_entity_platform(hass, f"sensor.{config_entry.domain}", platform)
    assert await entity_platform.async_setup_entry(config_entry)


# @pytest.mark.asyncio
# async def test_remove_entry(hass, manager):
#     """Test that we can remove an entry."""

#     async def mock_setup_entry(hass, entry):
#         """Mock setting up entry."""
#         hass.config_entries.async_setup_platforms(entry, ["sensor"])
#         return True

#     async def mock_unload_entry(hass, entry):
#         """Mock unloading an entry."""
#         result = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
#         assert result
#         return result

#     mock_remove_entry = AsyncMock(return_value=None)

#     entity = MockEntity(unique_id="1234", name="hugo")

#     async def mock_setup_entry_platform(hass, entry, async_add_entities):
#         """Mock setting up platform."""
#         async_add_entities([entity])

#     mock_integration(
#         hass,
#         MockModule(
#             "magnus",
#             async_setup_entry=mock_setup_entry,
#             async_unload_entry=mock_unload_entry,
#             async_remove_entry=mock_remove_entry,
#         ),
#     )
#     mock_entity_platform(
#         hass, "sensor.magnus", MockPlatform(async_setup_entry=mock_setup_entry_platform)
#     )
#     mock_entity_platform(hass, "config_flow.magnus", None)

#     #MockConfigEntry(domain="magnus", entry_id="test1").add_to_manager(manager)
#     entry = MockConfigEntry(domain="magnus", entry_id="test2")
#     entry.add_to_manager(manager)
#     # MockConfigEntry(domain="test_other", entry_id="test3").add_to_manager(manager)

#     # Check all config entries exist
#     assert [item.entry_id for item in manager.async_entries()] == [
#         #"test1",
#         "test2",
#         #"test3",
#     ]

#     # Setup entry
#     await entry.async_setup(hass)
#     await hass.async_block_till_done()

#     # Check entity state got added
#     #assert hass.states.get("sensor.hugo") is not None    
#     #assert len(hass.states.async_all()) == 1

#     # Check entity got added to entity registry
#     ent_reg = er.async_get(hass)
#     assert len(ent_reg.entities) == 1
#     #entity_entry = list(ent_reg.entities.values())[0]
#     #assert entity_entry.config_entry_id == entry.entry_id

#     # Remove entry
#     #result = await manager.async_remove("test2")
#     #await hass.async_block_till_done()

#     # Check that unload went well and so no need to restart
#     #assert result == {"require_restart": False}

#     # Check the remove callback was invoked.
#     #assert mock_remove_entry.call_count == 1

#     # Check that config entry was removed.
#     #assert [item.entry_id for item in manager.async_entries()] == ["test1", "test3"]

#     # Check that entity state has been removed
#     #assert hass.states.get("light.test_entity") is None
#     #assert len(hass.states.async_all()) == 0

#     # Check that entity registry entry has been removed
#     #entity_entry_list = list(ent_reg.entities.values())
#     #assert not entity_entry_list

# @pytest.mark.asyncio
# async def test_setup_entry(hass) -> None:
#     config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

#     assert await async_setup_component(hass, "sensor", CHARGEAMPS_CONFIG)
#     entity_reg = er.async_get(hass)
#     assert await entity_reg.async_get("sensor.chargeamps_123456M_1_power")
#     config_entry
#     assert await async_setup_entry(hass, config_entry)
#     assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]

# def test_chargeamps_halo(hass):
#     options = HubOptions()
#     options.charger.chargertype = "Chargeamps"
#     options.charger.chargerid = "1234567890A"
#     c = ChargerTypeData(
#             hass=hass,
#             input_type=options.charger.chargertype,
#             options=options
#         )
#     assert c.type.value == "chargeamps"

# @pytest.mark.asyncio
# async def test_unique_id(hass: HomeAssistant) -> None:
#     """Testing a default setup with unique_id"""

#     CONFIG = copy.deepcopy(VALID_CONFIG)
#     CONFIG["sensor"]["unique_id"] = "Testing123"

#     assert await async_setup_component(hass, "sensor", CONFIG)
    
#     entity_reg = er.async_get(hass)
#     print(entity_reg)
#     assert await entity_reg.async_get("sensor.peaqev_chargecontroller").unique_id == "Testing123"

# @pytest.mark.asyncio
# async def test_new_config(hass: HomeAssistant) -> None:
#     """Testing a default setup of an energyscore sensor"""
#     assert await async_setup_component(hass, "sensor", VALID_CONFIG)
#     await hass.async_block_till_done()

#     state = hass.states.get("sensor.peaqev_chargecontroller")
#     assert state.attributes.get("unit_of_measurement") == "%"
#     # assert state.attributes.get("state_class") == sensor.SensorStateClass.MEASUREMENT
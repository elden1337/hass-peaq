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
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.peaqev.__init__ import async_setup_entry


DOMAIN = "peaqev"
MOCK_CONFIG = {
"locale": "Göteborg",
"chargertype": "Chargeamps",
"chargerid": "test123",
"startpeaks": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 1, "9": 1, "10": 1, "11": 1, "12": 1},
"cautionhour_type": "suave",
"name": "sensor.power_meter"
}
# VALID_CONFIG = {
#         "sensor": {
#             "platform": "peaqev",
#             "name": "ChargeController",
#         }
#     }


@pytest.mark.asyncio
async def test_setup_entry(hass) -> None:
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

    assert await async_setup_entry(hass, config_entry)
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    #assert isinstance(hass.data[DOMAIN][config_entry.entry_id], ShlDataUpdateCoordinator)

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
"""Tests for Hub core models: HubModel, HubOptions, EventProperty."""
from datetime import datetime, timedelta

import pytest
from peaqevcore.common.spotprice.models.spotprice_type import SpotPriceType

from custom_components.peaqev.peaqservice.hub.models.event_property import \
    EventProperty
from custom_components.peaqev.peaqservice.hub.models.hub_model import HubModel
from custom_components.peaqev.peaqservice.hub.models.hub_options import (
    Charger, HubOptions, Price)
from custom_components.peaqev.peaqservice.util.options_comparer import \
    OptionsComparer
from custom_components.peaqev.test.conftest import MockHass

# --- EventProperty Tests ---

@pytest.mark.asyncio
async def test_eventproperty_initial_value(mock_hass):
    prop = EventProperty("test_prop", str, mock_hass, default="initial")
    assert prop.value == "initial"


@pytest.mark.asyncio
async def test_eventproperty_set_value_triggers_bus(mock_hass):
    prop = EventProperty("test_prop", str, mock_hass)
    prop.value = "new_value"
    assert mock_hass.bus.fire.called
    call_args = mock_hass.bus.fire.call_args
    assert "peaqev.test_prop" in call_args[0][0]
    assert call_args[0][1].get("new") == "new_value"


@pytest.mark.asyncio
async def test_eventproperty_bool_timeout_expiration(mock_hass):
    prop = EventProperty("bool_prop", bool, mock_hass, default=False)
    prop.value = True
    future_timeout = datetime.now() + timedelta(seconds=10)
    prop.timeout = future_timeout
    assert prop.value == True

    past_timeout = datetime.now() - timedelta(seconds=10)
    prop.timeout = past_timeout
    assert prop.value == False


@pytest.mark.asyncio
async def test_eventproperty_bool_no_timeout(mock_hass):
    prop = EventProperty("bool_prop", bool, mock_hass, default=True)
    assert prop.value == True


@pytest.mark.asyncio
async def test_eventproperty_non_bool_type_ignores_timeout(mock_hass):
    prop = EventProperty("string_prop", str, mock_hass, default="test")
    past_timeout = datetime.now() - timedelta(seconds=10)
    prop.timeout = past_timeout
    assert prop.value == "test"


@pytest.mark.asyncio
async def test_eventproperty_timeout_property(mock_hass):
    prop = EventProperty("test", str, mock_hass)
    assert prop.timeout is None
    prop.timeout = datetime.now()
    assert prop.timeout is not None


@pytest.mark.asyncio
async def test_eventproperty_name_property(mock_hass):
    prop = EventProperty("my_name", str, mock_hass)
    assert prop.name == "my_name"


# --- HubModel Tests ---

@pytest.mark.asyncio
async def test_hubmodel_creates_event_property(mock_hass):
    model = HubModel(domain="test_domain", hass=mock_hass)
    assert model.peak_breached is not None
    assert isinstance(model.peak_breached, EventProperty)


@pytest.mark.asyncio
async def test_hubmodel_chargingtracker_entities_default():
    model = HubModel(domain="test", hass=MockHass())
    assert model.chargingtracker_entities == []


@pytest.mark.asyncio
async def test_hubmodel_peak_breached_setter_triggers_bus(mock_hass):
    model = HubModel(domain="test", hass=mock_hass)
    model.peak_breached.value = True
    assert mock_hass.bus.fire.called


@pytest.mark.asyncio
async def test_hubmodel_peak_breached_bool_timeout(mock_hass):
    model = HubModel(domain="test", hass=mock_hass)
    model.peak_breached.value = True
    future_timeout = datetime.now() + timedelta(seconds=10)
    model.peak_breached.timeout = future_timeout
    assert model.peak_breached.value == True


# --- HubOptions Tests ---

@pytest.mark.asyncio
async def test_huboptions_default_initialization():
    options = HubOptions()
    assert options.peaqev_lite == False
    assert options.powersensor_includes_car == False
    assert options.max_charge == 0
    assert options.gainloss == False
    assert options.use_peak_history == False
    assert options.fuse_type == ''


@pytest.mark.asyncio
async def test_huboptions_post_init_creates_subobjects():
    options = HubOptions()
    assert isinstance(options.charger, Charger)
    assert isinstance(options.price, Price)


@pytest.mark.asyncio
async def test_huboptions_startpeaks_setter():
    options = HubOptions()
    raw_peaks = {"1": 100, "2": 200, "3": 300}
    options.startpeaks = raw_peaks
    assert options.startpeaks == {1: 100, 2: 200, 3: 300}


@pytest.mark.asyncio
async def test_huboptions_startpeaks_empty_dict():
    options = HubOptions()
    options.startpeaks = {}
    assert options.startpeaks == {}


@pytest.mark.asyncio
async def test_huboptions_compare_no_diff():
    options1 = HubOptions()
    options2 = HubOptions()
    options1._startpeaks = {}
    options2._startpeaks = {}
    diff = options1.compare(options2)
    assert diff == []


@pytest.mark.asyncio
async def test_huboptions_compare_with_diff():
    options1 = HubOptions()
    options1.peaqev_lite = True
    options2 = HubOptions()
    diff = options1.compare(options2)
    assert 'peaqev_lite' in diff


@pytest.mark.asyncio
async def test_huboptions_compare_price_diff():
    options1 = HubOptions()
    options1.price.price_aware = True
    options2 = HubOptions()
    diff = options1.compare(options2)
    assert 'price_aware' in diff


@pytest.mark.asyncio
async def test_huboptions_compare_charger_diff():
    options1 = HubOptions()
    options1.charger.chargertype = 'Easee'
    options2 = HubOptions()
    diff = options1.compare(options2)
    assert 'chargertype' in diff


@pytest.mark.asyncio
async def test_huboptions_compare_with_startpeaks():
    options1 = HubOptions()
    options1.startpeaks = {1: 100}
    options2 = HubOptions()
    diff = options1.compare(options2)
    assert '_startpeaks' in diff


# --- Price Tests ---

@pytest.mark.asyncio
async def test_price_default_values():
    price = Price()
    assert price.price_aware == False
    assert price.min_price == 0.0
    assert price.top_price == 0.0
    assert price.cautionhour_type == ''
    assert price.dynamic_top_price == False
    assert price.spotprice_type == SpotPriceType.Auto


@pytest.mark.asyncio
async def test_price_with_values():
    price = Price(
        price_aware=True,
        min_price=1.5,
        top_price=5.0,
        cautionhour_type='caution',
        dynamic_top_price=True
    )
    assert price.price_aware == True
    assert price.min_price == 1.5
    assert price.top_price == 5.0


# --- Charger Tests ---

@pytest.mark.asyncio
async def test_charger_default_values():
    charger = Charger()
    assert charger.chargertype == ''
    assert charger.chargerid == ''
    assert charger.powerswitch == ''
    assert charger.powermeter == ''


@pytest.mark.asyncio
async def test_charger_with_values():
    charger = Charger(
        chargertype="Easee",
        chargerid="easee_001",
        powerswitch="switch.charger",
        powermeter="sensor.charger_power"
    )
    assert charger.chargertype == "Easee"
    assert charger.chargerid == "easee_001"


# --- OptionsComparer Tests ---

@pytest.mark.asyncio
async def test_options_comparer_compare_no_keys():
    class SimpleOpts(OptionsComparer):
        def __init__(self):
            self.a = 1
            self.b = 2

    opts1 = SimpleOpts()
    opts2 = SimpleOpts()
    diff = opts1.compare(opts2)
    assert diff == []


@pytest.mark.asyncio
async def test_options_comparer_compare_with_extra_key():
    class SimpleOpts(OptionsComparer):
        def __init__(self):
            self.a = 1
            self.b = 2

    opts1 = SimpleOpts()
    opts1.c = 3
    opts2 = SimpleOpts()
    diff = opts1.compare(opts2)
    assert 'c' in diff


@pytest.mark.asyncio
async def test_options_comparer_compare_value_diff():
    class SimpleOpts(OptionsComparer):
        def __init__(self):
            self.a = 1

    opts1 = SimpleOpts()
    opts1.a = 5
    opts2 = SimpleOpts()
    diff = opts1.compare(opts2)
    assert 'a' in diff

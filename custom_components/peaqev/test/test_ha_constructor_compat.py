"""Tests that sensors adapt to the HA-core constructor change in 2026.8.

Home Assistant 2026.8 removed the `hass` parameter from
`IntegrationSensor.__init__` and `UtilityMeterSensor.__init__` and made the
remaining parameters keyword-only. The sensors here must construct on both
sides of that change, so `hass` is only forwarded while the installed core
still accepts it.
"""
import inspect
from unittest.mock import MagicMock

import pytest
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from peaqevcore.models.locale.enums.time_periods import TimePeriods

from custom_components.peaqev.sensors.integration_sensor import (
    PeaqIntegrationCostSensor, PeaqIntegrationSensor)
from custom_components.peaqev.sensors.utility_sensor import \
    async_create_single_utility

# Constructors as of home-assistant/core tag 2026.8.1.


def _integration_2026_8(self, *, integration_method, name, round_digits, source_entity,
                        unique_id, unit_prefix, unit_time, max_sub_interval, device=None):
    ...


def _utility_meter_2026_8(self, *, cron_pattern, delta_values, meter_offset, meter_type,
                          name, net_consumption, parent_meter, periodically_resetting,
                          source_entity, tariff_entity, tariff, unique_id,
                          sensor_always_available, suggested_entity_id=None, device=None):
    ...


def _patch_init(monkeypatch, cls, signature_source, captured: dict) -> None:
    """Replace cls.__init__ with a recorder that enforces signature_source."""
    signature = inspect.signature(signature_source)

    def __init__(self, *args, **kwargs):
        captured.update(kwargs)
        signature.bind(self, *args, **kwargs)  # TypeError on any mismatch
        self._attr_unique_id = kwargs.get('unique_id')
        self._attr_native_value = None

    __init__.__signature__ = signature
    monkeypatch.setattr(cls, '__init__', __init__)


@pytest.fixture
def hub():
    ret = MagicMock()
    ret.hubname = 'Peaqev'
    ret.hub_id = 1234
    return ret


@pytest.mark.parametrize('signature_source, expect_hass', [
    (IntegrationSensor.__init__, 'hass' in inspect.signature(IntegrationSensor.__init__).parameters),
    (_integration_2026_8, False),
])
def test_integration_sensors_match_installed_signature(monkeypatch, hub, signature_source, expect_hass):
    captured: dict = {}
    _patch_init(monkeypatch, IntegrationSensor, signature_source, captured)
    hass = MagicMock()

    PeaqIntegrationCostSensor(hass, hub, 'cost integral', 'entry_id')
    assert ('hass' in captured) is expect_hass

    captured.clear()
    PeaqIntegrationSensor(hass, hub, 'sensor.foo', 'name', 'entry_id')
    assert ('hass' in captured) is expect_hass


@pytest.mark.asyncio
@pytest.mark.parametrize('signature_source, expect_hass', [
    (UtilityMeterSensor.__init__, 'hass' in inspect.signature(UtilityMeterSensor.__init__).parameters),
    (_utility_meter_2026_8, False),
])
async def test_utility_sensor_matches_installed_signature(monkeypatch, hub, signature_source, expect_hass):
    captured: dict = {}
    _patch_init(monkeypatch, UtilityMeterSensor, signature_source, captured)

    await async_create_single_utility(
        MagicMock(), hub, 'foo', TimePeriods.Daily, 'entry_id'
    )
    assert ('hass' in captured) is expect_hass


@pytest.mark.asyncio
async def test_utility_sensor_keeps_device_link_on_2026_8(monkeypatch, hub):
    """2026.8 expects the caller to resolve the device hass was used for."""
    captured: dict = {}
    _patch_init(monkeypatch, UtilityMeterSensor, _utility_meter_2026_8, captured)
    device = object()
    monkeypatch.setattr(
        'custom_components.peaqev.sensors.utility_sensor.async_entity_id_to_device',
        lambda hass, entity_id: device,
    )

    await async_create_single_utility(
        MagicMock(), hub, 'foo', TimePeriods.Daily, 'entry_id'
    )
    assert captured['device'] is device

"""Restored states are frequently 'unknown'/'unavailable'.

Raising in async_added_to_hass makes Home Assistant drop the entity, so a
sensor that fails to restore disappears until the next restart. These tests
cover the entities that read a number back out of their previous state.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.peaqev.number import (PeaqMaxMinLimiterNumber,
                                             PeaqSchedulerChargeAmountNumber)
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    try_parse_float
from custom_components.peaqev.select import PeaqSelectEntity
from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
from custom_components.peaqev.sensors.session_sensor import (
    PeaqSessionCostSensor, PeaqSessionSensor)

BAD_STATES = [STATE_UNKNOWN, STATE_UNAVAILABLE, '', None]

RESTORE_TARGET = 'homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state'


@pytest.mark.parametrize('value, expected', [
    ('12.5', 12.5), ('0', 0.0), (7, 7.0),
    (STATE_UNKNOWN, None), (STATE_UNAVAILABLE, None), ('', None), (None, None),
])
def test_try_parse_float(value, expected):
    assert try_parse_float(value) == expected


def _restore(value):
    """Patch what RestoreEntity hands back; the entities call it via super()."""
    state = MagicMock()
    state.state = value
    state.attributes = {}
    return patch(RESTORE_TARGET, new=AsyncMock(return_value=state))


def _hub():
    hub = MagicMock()
    hub.hubname = 'Peaqev'
    hub.chargecontroller.session = AsyncMock()
    return hub


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', BAD_STATES)
async def test_average_sensor_survives_bad_restore(bad):
    sensor = PeaqAverageSensor(_hub(), 'entry', 'average consumption', 60)
    with _restore(bad):
        await sensor.async_added_to_hass()
    assert sensor.state is None


@pytest.mark.asyncio
async def test_average_sensor_restores_a_number():
    sensor = PeaqAverageSensor(_hub(), 'entry', 'average consumption', 60)
    with _restore('1234.5'):
        await sensor.async_added_to_hass()
    assert sensor.state == 1234.5


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', BAD_STATES)
async def test_session_sensors_survive_bad_restore(bad):
    hub = _hub()
    energy = PeaqSessionSensor(hub, 'entry')
    with _restore(bad):
        await energy.async_added_to_hass()
    hub.chargecontroller.session.async_setup_fresh.assert_awaited()

    cost = PeaqSessionCostSensor(hub, 'entry')
    with _restore(bad):
        await cost.async_added_to_hass()
    assert cost.state == 0


@pytest.mark.asyncio
async def test_session_sensor_restores_a_number():
    hub = _hub()
    energy = PeaqSessionSensor(hub, 'entry')
    with _restore('4.2'):
        await energy.async_added_to_hass()
    hub.chargecontroller.session.async_set_session_energy.assert_awaited_with(4.2)
    assert hub.chargecontroller.charger.model.session_active is True


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', BAD_STATES)
@pytest.mark.parametrize('cls', [PeaqSchedulerChargeAmountNumber, PeaqMaxMinLimiterNumber])
async def test_number_entities_survive_bad_restore(bad, cls):
    number = cls('max charge', _hub())
    with _restore(bad):
        await number.async_added_to_hass()
    assert number.native_value == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', BAD_STATES)
async def test_select_ignores_a_restored_non_option(bad):
    scheduler = MagicMock()
    scheduler.display_options = ['No schedule', '07:00']
    scheduler.async_handle_scheduler_departure_option = AsyncMock()

    select = PeaqSelectEntity('Scheduler next departure', scheduler)
    with _restore(bad):
        await select.async_added_to_hass()

    assert select.current_option == 'No schedule'
    scheduler.async_handle_scheduler_departure_option.assert_not_awaited()


@pytest.mark.asyncio
async def test_select_restores_a_known_option():
    scheduler = MagicMock()
    scheduler.display_options = ['No schedule', '07:00']
    scheduler.async_handle_scheduler_departure_option = AsyncMock()

    select = PeaqSelectEntity('Scheduler next departure', scheduler)
    with _restore('07:00'):
        await select.async_added_to_hass()

    assert select.current_option == '07:00'
    scheduler.async_handle_scheduler_departure_option.assert_awaited_with('07:00')

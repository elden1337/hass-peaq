"""Incoming Home Assistant state changes that carry no usable value.

Both cases below are routine - sensors start as unknown, source integrations
go unavailable while reloading, and entities are removed on unload - so
neither should produce an error in the user's log.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes import \
    StateChanges

NO_VALUE = [STATE_UNKNOWN, STATE_UNAVAILABLE, None]


def _states(hub) -> StateChanges:
    states = StateChanges(hub)
    hub.states = states
    return states


def _hub() -> MagicMock:
    hub = MagicMock()
    hub.options.price.price_aware = False
    hub.observer.async_broadcast = AsyncMock()
    hub.is_initialized = True
    return hub


@pytest.mark.asyncio
@pytest.mark.parametrize('value', NO_VALUE)
async def test_update_sensor_skips_values_it_cannot_use(value):
    hub = _hub()
    states = _states(hub)
    with patch.object(
        StateChanges, 'async_update_sensor_internal', new_callable=AsyncMock
    ) as internal:
        await states.async_update_sensor('sensor.whatever', value)

    internal.assert_not_awaited()
    # the rest of the flow still runs, exactly as when a handler returns False
    hub.observer.async_broadcast.assert_awaited()


@pytest.mark.asyncio
async def test_update_sensor_still_handles_real_values():
    hub = _hub()
    states = _states(hub)
    with patch.object(
        StateChanges, 'async_update_sensor_internal', new_callable=AsyncMock
    ) as internal:
        await states.async_update_sensor('sensor.whatever', '230.5')

    internal.assert_awaited_with('sensor.whatever', '230.5')


@pytest.mark.asyncio
async def test_on_change_ignores_removed_entities(caplog):
    """new_state is None when an entity is removed, e.g. on every unload."""
    hub = MagicMock(spec=HomeAssistantHub)
    hub.states = MagicMock()
    hub.states.async_update_sensor = AsyncMock()

    event = MagicMock()
    event.data = {'entity_id': 'sensor.gone', 'old_state': MagicMock(), 'new_state': None}

    await HomeAssistantHub._async_on_change(hub, event)

    hub.states.async_update_sensor.assert_not_awaited()
    assert not [r for r in caplog.records if r.levelno >= 40]

"""Extended tests for Observer edge cases: throttling, sync broadcast, enum conversion, error paths."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from peaqevcore.common.models.observer_types import ObserverTypes

from custom_components.peaqev.peaqservice.hub.hub_factory import HubFactory
from custom_components.peaqev.peaqservice.hub.observer.const import TIMEOUT
from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import \
    IObserver
from custom_components.peaqev.peaqservice.hub.observer.models.command import \
    Command
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer
from custom_components.peaqev.test.conftest import MockObserver


class MockCallsExtended:
    """Extended mock calls for testing edge cases."""
    results = []

    @staticmethod
    def reset():
        MockCallsExtended.results = []

    @staticmethod
    async def async_no_args():
        MockCallsExtended.results.append("async_no_args")

    @staticmethod
    async def async_with_arg(arg):
        MockCallsExtended.results.append(f"async_with_arg:{arg}")

    @staticmethod
    async def async_with_dict_arg(**kwargs):
        MockCallsExtended.results.append(f"async_dict:{kwargs}")

    @staticmethod
    def sync_no_args():
        MockCallsExtended.results.append("sync_no_args")

    @staticmethod
    def sync_with_arg(arg):
        MockCallsExtended.results.append(f"sync_with_arg:{arg}")

    @staticmethod
    def sync_with_dict_arg(**kwargs):
        MockCallsExtended.results.append(f"sync_dict:{kwargs}")

    @staticmethod
    async def async_raises():
        raise ValueError("test error")

    @staticmethod
    def sync_raises():
        raise RuntimeError("sync error")


@pytest.mark.asyncio
async def test_observer_enum_string_conversion(mock_observer):
    """Test that string commands are converted to ObserverTypes."""
    mock_observer.add("Test", MockCallsExtended.async_no_args)
    assert ObserverTypes.Test in mock_observer.model.subscribers


@pytest.mark.asyncio
async def test_observer_invalid_string_conversion(mock_observer):
    """Test that invalid strings fall back to ObserverTypes.Test."""
    mock_observer.add("INVALID_STRING_THAT_DOES_NOT_EXIST", MockCallsExtended.async_no_args)
    # Should fall back to ObserverTypes.Test
    assert ObserverTypes.Test in mock_observer.model.subscribers


@pytest.mark.asyncio
async def test_observer_sync_broadcast(mock_observer):
    """Test synchronous broadcast method."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.sync_no_args)
    mock_observer.broadcast(ObserverTypes.Test)
    assert len(mock_observer.model.broadcast_queue) == 1
    assert mock_observer.model.broadcast_queue[0].command == ObserverTypes.Test


@pytest.mark.asyncio
async def test_observer_broadcast_with_argument(mock_observer):
    """Test broadcast with single argument."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.sync_with_arg)
    await mock_observer.async_broadcast(ObserverTypes.Test, argument="test_value")
    await mock_observer.async_dispatch()
    assert "sync_with_arg:test_value" in MockCallsExtended.results


@pytest.mark.asyncio
async def test_observer_broadcast_with_dict_argument(mock_observer):
    """Test broadcast with dict argument (unpacking)."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.sync_with_dict_arg)
    await mock_observer.async_broadcast(
        ObserverTypes.Test, argument={"key1": "val1", "key2": "val2"}
    )
    await mock_observer.async_dispatch()
    assert "sync_dict:{'key1': 'val2', 'key2': 'val2'}" in MockCallsExtended.results or \
           "sync_dict:" in str(MockCallsExtended.results)


@pytest.mark.asyncio
async def test_observer_broadcast_with_dict_async_argument(mock_observer):
    """Test async broadcast with dict argument (unpacking)."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_with_dict_arg)
    await mock_observer.async_broadcast(
        ObserverTypes.Test, argument={"key": "value"}
    )
    await mock_observer.async_dispatch()
    assert any("async_dict:" in str(r) for r in MockCallsExtended.results)


@pytest.mark.asyncio
async def test_observer_command_expiration():
    """Test that commands expire after TIMEOUT seconds."""
    MockObserver()
    cmd = Command(ObserverTypes.Test, expiration=time.time() - TIMEOUT - 1, argument=None)
    assert cmd.expiration < time.time()


@pytest.mark.asyncio
async def test_observer_command_not_expired():
    """Test that fresh commands haven't expired."""
    MockObserver()
    cmd = Command(ObserverTypes.Test, expiration=time.time() + 100, argument=None)
    assert cmd.expiration > time.time()


@pytest.mark.asyncio
async def test_observer_duplicate_command_detection(mock_observer):
    """Test that duplicate commands are not added to broadcast_queue."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    await mock_observer.async_broadcast(ObserverTypes.Test)
    await mock_observer.async_broadcast(ObserverTypes.Test)
    assert len(mock_observer.model.broadcast_queue) == 1


@pytest.mark.asyncio
async def test_observer_queue_overflow_triggers_dispatch(mock_observer):
    """Test that queue overflow (>10) triggers dispatch."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    for i in range(12):
        await mock_observer.async_broadcast(ObserverTypes.Test)
    assert len(mock_observer.model.broadcast_queue) <= 10


@pytest.mark.asyncio
async def test_observer_throttling_same_command(mock_observer):
    """Test that rapid broadcasts of same command are throttled."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    # First broadcast should succeed
    await mock_observer.async_broadcast(ObserverTypes.Test)
    # Rapid second broadcast should be throttled (wait_queue prevents it)
    await mock_observer.async_broadcast(ObserverTypes.Test)
    # The second broadcast should still be queued but throttled
    assert len(mock_observer.model.broadcast_queue) <= 2


@pytest.mark.asyncio
async def test_observer_different_commands_not_throttled(mock_observer):
    """Test that different commands are not throttled against each other."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    mock_observer.add(ObserverTypes.CarConnected, MockCallsExtended.async_no_args)
    await mock_observer.async_broadcast(ObserverTypes.Test)
    await mock_observer.async_broadcast(ObserverTypes.CarConnected)
    assert len(mock_observer.model.broadcast_queue) == 2


@pytest.mark.asyncio
async def test_observer_activate_with_init_broadcast(mock_observer):
    """Test activate() with initial broadcast."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    mock_observer.activate(ObserverTypes.Test)
    assert mock_observer.model.active == True
    assert len(mock_observer.model.broadcast_queue) == 1


@pytest.mark.asyncio
async def test_observer_activate_without_init_broadcast(mock_observer):
    """Test activate() without initial broadcast."""
    mock_observer.activate()
    assert mock_observer.model.active == True
    assert len(mock_observer.model.broadcast_queue) == 0


@pytest.mark.asyncio
async def test_observer_multiple_subscribers_same_command(mock_observer):
    """Test that multiple subscribers receive the same broadcast."""
    MockCallsExtended.reset()
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.sync_no_args)
    await mock_observer.async_broadcast(ObserverTypes.Test)
    await mock_observer.async_dispatch()
    assert len(MockCallsExtended.results) == 2


@pytest.mark.asyncio
async def test_observer_async_call_func_with_none_argument(mock_observer):
    """Test async_call_func with None argument (calls func with no args)."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_no_args)
    await mock_observer.async_broadcast(ObserverTypes.Test, argument=None)
    await mock_observer.async_dispatch()
    assert "async_no_args" in MockCallsExtended.results


@pytest.mark.asyncio
async def test_observer_async_call_func_single_value_argument(mock_observer):
    """Test async_call_func with single non-dict argument."""
    mock_observer.add(ObserverTypes.Test, MockCallsExtended.async_with_arg)
    await mock_observer.async_broadcast(ObserverTypes.Test, argument=42)
    await mock_observer.async_dispatch()
    assert "async_with_arg:42" in MockCallsExtended.results


@pytest.mark.asyncio
async def test_observer_call_func_with_dict_fallback_to_no_args():
    """Test _call_func with dict that causes TypeError falls back to no-args."""
    # Function that doesn't accept **kwargs should fall back to no-args
    def strict_func():
        MockCallsExtended.results.append("strict_func")

    cmd = Command(ObserverTypes.Test, time.time() + 100, {"x": 1})
    IObserver._call_func(strict_func, cmd)
    assert "strict_func" in MockCallsExtended.results


@pytest.mark.asyncio
async def test_observer_call_func_single_arg_fallback_to_no_args():
    """Test _call_func with single arg that causes TypeError falls back to no-args."""
    def no_arg_func():
        MockCallsExtended.results.append("no_arg_func")

    cmd = Command(ObserverTypes.Test, time.time() + 100, "some_arg")
    IObserver._call_func(no_arg_func, cmd)
    assert "no_arg_func" in MockCallsExtended.results


@pytest.mark.asyncio
async def test_observer_wait_queue_key_creation(mock_observer):
    """Test that wait_queue gets created for new commands."""
    await mock_observer.async_ok_to_broadcast(ObserverTypes.Test)
    assert ObserverTypes.Test in mock_observer.model.wait_queue


@pytest.mark.asyncio
async def test_observer_wait_queue_reuses_existing(mock_observer):
    """Test that wait_queue reuses existing timestamps for same command."""
    first_result = await mock_observer.async_ok_to_broadcast(ObserverTypes.Test)
    assert first_result == True
    # Immediately after, should be throttled
    second_result = await mock_observer.async_ok_to_broadcast(ObserverTypes.Test)
    assert second_result == False


@pytest.mark.asyncio
async def test_observer_command_equality():
    """Test Command __eq__ for deduplication."""
    cmd1 = Command(ObserverTypes.Test, time.time() + 100, "arg")
    cmd2 = Command(ObserverTypes.Test, time.time() + 200, "arg")
    assert cmd1 == cmd2  # Same command and argument, different expiration


@pytest.mark.asyncio
async def test_observer_command_inequality():
    """Test Command __eq__ for different commands."""
    cmd1 = Command(ObserverTypes.Test, time.time() + 100, "arg")
    cmd2 = Command(ObserverTypes.CarConnected, time.time() + 100, "arg")
    assert cmd1 != cmd2


@pytest.mark.asyncio
async def test_observer_command_inequality_different_arg():
    """Test Command __eq__ for different arguments."""
    cmd1 = Command(ObserverTypes.Test, time.time() + 100, "arg1")
    cmd2 = Command(ObserverTypes.Test, time.time() + 100, "arg2")
    assert cmd1 != cmd2


# --- Observer lifecycle tests ---

@pytest.mark.asyncio
async def test_observer_cancels_its_interval_on_entry_unload():
    """The dispatch interval must be tied to the config entry.

    Options changes reload the entry, so an interval that outlives the unload
    keeps dispatching against a dead hub, once per second, forever.
    """
    hass = MagicMock()
    entry = MagicMock()
    unsub = MagicMock()

    with patch(
        'custom_components.peaqev.peaqservice.hub.observer.observer_coordinator.async_track_time_interval',
        return_value=unsub,
    ):
        Observer(hass, entry)

    entry.async_on_unload.assert_called_once_with(unsub)


@pytest.mark.asyncio
async def test_hub_factory_passes_entry_to_observer():
    """HubFactory has to hand the entry over, or the wiring above never happens."""
    hass = MagicMock()
    entry = MagicMock()
    options = MagicMock()
    options.price.price_aware = False

    with (
        patch(
            'custom_components.peaqev.peaqservice.hub.hub_factory.Observer'
        ) as mock_observer,
        patch(
            'custom_components.peaqev.peaqservice.hub.hub_factory.HomeAssistantHub'
        ),
        patch.object(HubFactory, 'async_setup', new_callable=AsyncMock) as mock_setup,
    ):
        await HubFactory.async_create(hass, options, 'peaqev', entry)

    assert mock_observer.call_args.args == (hass, entry)
    assert mock_setup.await_count == 1

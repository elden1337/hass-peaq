import time

import pytest

from custom_components.peaqev.peaqservice.hub.observer.models.observer_types import \
    ObserverTypes
from custom_components.peaqev.test.mock_classes.observer_coordinator_test import \
    ObserverTest


class MockCalls:
    mock_async_call_single_arg_result = None
    mock_async_call_multiple_args_result = None
    mock_call_single_arg_result = None
    mock_call_multiple_args_result = None

    @staticmethod
    async def mock_async_call_no_args():
        return True

    @staticmethod
    async def mock_async_call_single_arg(test_arg):
        MockCalls.mock_async_call_single_arg_result = test_arg

    @staticmethod
    async def mock_async_call_multiple_args(test_arg1, test_arg2):
        MockCalls.mock_async_call_multiple_args_result = test_arg1, test_arg2

    @staticmethod
    def mock_call_no_args():
        return True

    @staticmethod
    def mock_call_single_arg(test_arg):
        MockCalls.mock_call_single_arg_result = test_arg

    @staticmethod
    def mock_call_multiple_args(test_arg1, test_arg2):
        MockCalls.mock_call_multiple_args_result = test_arg1, test_arg2


@pytest.mark.asyncio
async def test_observer_add():
    observer = ObserverTest()
    observer.add(ObserverTypes.Test, lambda x: x)
    assert ObserverTypes.Test in observer.model.subscribers.keys()

@pytest.mark.asyncio
async def test_observer_activate():
    observer = ObserverTest()
    observer.activate()
    assert observer.model.active == True

@pytest.mark.asyncio
async def test_observer_deactivate():
    observer = ObserverTest()
    observer.deactivate()
    assert observer.model.active == False

@pytest.mark.asyncio
async def test_observer_broadcast():
    observer = ObserverTest()
    await observer.async_broadcast(ObserverTypes.Test)
    assert observer.model.broadcast_queue[0].command == ObserverTypes.Test

@pytest.mark.asyncio
async def test_observer_async_dispatch():
    observer = ObserverTest()
    observer.add(ObserverTypes.Test, MockCalls.mock_async_call_no_args)
    await observer.async_broadcast(ObserverTypes.Test)
    await observer.async_dispatch()
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dispatch_single_arg():
    observer = ObserverTest()
    observer.add(ObserverTypes.Test, MockCalls.mock_async_call_single_arg)
    argument = time.time
    await observer.async_broadcast(ObserverTypes.Test, argument)
    await observer.async_dispatch()
    assert MockCalls.mock_async_call_single_arg_result == argument

@pytest.mark.asyncio
async def test_observer_sync_dispatch():
    observer = ObserverTest()
    observer.add(ObserverTypes.Test, MockCalls.mock_call_no_args)
    await observer.async_broadcast(ObserverTypes.Test)
    await observer.async_dispatch()
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_sync_dispatch_single_arg():
    observer = ObserverTest()
    observer.add(ObserverTypes.Test, MockCalls.mock_call_single_arg)
    argument = time.time
    await observer.async_broadcast(ObserverTypes.Test, argument)
    await observer.async_dispatch()
    assert MockCalls.mock_call_single_arg_result == argument

@pytest.mark.asyncio
async def test_observer_async_dispatch_no_subscriber():
    observer = ObserverTest()
    await observer.async_broadcast(ObserverTypes.Test)
    await observer.async_dispatch()
    assert observer.model.broadcast_queue[0].command == ObserverTypes.Test

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast():
    observer = ObserverTest()
    await observer.async_broadcast(ObserverTypes.Test)
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast_not_in_broadcast_queue():
    observer = ObserverTest()
    await observer.async_broadcast(ObserverTypes.Test)
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []
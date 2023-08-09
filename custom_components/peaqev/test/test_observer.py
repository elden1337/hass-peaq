import pytest

from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    ObserverTest


async def mock_async_call_no_args():
    return True

async def mock_async_call_single_arg(test_arg):
    return test_arg

async def mock_async_call_multiple_args(test_arg1, test_arg2):
    return test_arg1, test_arg2

def mock_call_no_args():
    return True

def mock_call_single_arg(test_arg):
    return test_arg

def mock_call_multiple_args(test_arg1, test_arg2):
    return test_arg1, test_arg2


@pytest.mark.asyncio
async def test_observer_add():
    observer = ObserverTest()
    observer.add("test", lambda x: x)
    assert "test" in observer.model.subscribers.keys()

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
    await observer.async_broadcast("test")
    assert observer.model.broadcast_queue[0].command == "test"

@pytest.mark.asyncio
async def test_observer_async_dispatch():
    observer = ObserverTest()
    observer.add("test", mock_async_call_no_args)
    await observer.async_broadcast("test")
    await observer.async_dispatch()
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dispatch_no_subscriber():
    observer = ObserverTest()
    await observer.async_broadcast("test")
    await observer.async_dispatch()
    assert observer.model.broadcast_queue[0].command == "test"

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast():
    observer = ObserverTest()
    await observer.async_broadcast("test")
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast_not_in_broadcast_queue():
    observer = ObserverTest()
    await observer.async_broadcast("test")
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []
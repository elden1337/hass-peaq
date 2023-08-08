import pytest

from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer


@pytest.mark.asyncio
async def test_observer_add():
    observer = Observer(test=True)
    observer.add("test", lambda x: x)
    assert "test" in observer.model.subscribers.keys()

@pytest.mark.asyncio
async def test_observer_activate():
    observer = Observer(test=True)
    observer.activate()
    assert observer.model.active == True

@pytest.mark.asyncio
async def test_observer_deactivate():
    observer = Observer(test=True)
    observer.deactivate()
    assert observer.model.active == False

@pytest.mark.asyncio
async def test_observer_broadcast():
    observer = Observer(test=True)
    await observer.async_broadcast("test")
    assert observer.model.broadcast_queue[0].command == "test"

@pytest.mark.asyncio
async def test_observer_async_dispatch():
    observer = Observer(test=True)
    await observer.async_broadcast("test")
    await observer.async_dispatch()
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast():
    observer = Observer(test=True)
    await observer.async_broadcast("test")
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast_not_in_subscribers():
    observer = Observer(test=True)
    await observer.async_broadcast("test")
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []

@pytest.mark.asyncio
async def test_observer_async_dequeue_and_broadcast_not_in_broadcast_queue():
    observer = Observer(test=True)
    await observer.async_dequeue_and_broadcast(observer.model.broadcast_queue[0])
    assert observer.model.broadcast_queue == []
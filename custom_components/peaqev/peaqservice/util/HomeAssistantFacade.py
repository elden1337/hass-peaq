from abc import abstractmethod, ABC
from typing import Callable

from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers.event import async_track_state_change


class IHomeAssistantFacade(ABC):

    @abstractmethod
    def get_state(self, entitystr: str):
        pass

    @property
    @abstractmethod
    def loop(self):
        pass

    @abstractmethod
    def register_event_listener(self, event_type, listener):
        pass

    @abstractmethod
    def async_set_state(self, entity_id, state, attributes=None):
        pass

    @abstractmethod
    async def async_call_service(self, domain, service, data):
        pass

    @abstractmethod
    async def async_add_executor_job(self, function: Callable):
        pass

    @abstractmethod
    def async_track_state_change(self, trackers, callbackfunc: Callable):
        pass

    @abstractmethod
    def bus_fire(self, event_type, event_data):
        pass

    @abstractmethod
    def async_create_task(self, target):
        pass

    @abstractmethod
    def async_track_time_interval(self, callback, interval):
        pass

    @abstractmethod
    def async_register_service(self, DOMAIN, service, service_func, supports_response_str='none'):
        pass

class HomeAssistantFacade(IHomeAssistantFacade):
    def __init__(self, homeassistant: HomeAssistant):
        self.homeassistant = homeassistant

    @property
    def loop(self):
        return self.homeassistant.loop

    def get_state(self, entitystr: str):
        return self.homeassistant.states.get(entitystr)

    def async_set_state(self, entity_id, state, attributes=None):
        self.homeassistant.states.async_set(entity_id, state, attributes)

    def register_event_listener(self, event_type, listener):
        self.homeassistant.bus.async_listen(event_type, listener)

    async def async_call_service(self, domain, service, data):
        await self.homeassistant.services.async_call(domain, service, data)

    async def async_add_executor_job(self, function: Callable):
        await self.homeassistant.async_add_executor_job(function)

    def async_track_state_change(self, trackers, callbackfunc: Callable):
        async_track_state_change(self.homeassistant, trackers, callbackfunc)

    def bus_fire(self, event_type, event_data):
        self.homeassistant.bus.fire(event_type, event_data)

    def async_create_task(self, target):
        self.homeassistant.async_create_task(target=target)

    def async_register_service(self, DOMAIN, service, service_func, supports_response_str='none'):
        try:
            SupportsResponseEnum = SupportsResponse(supports_response_str)
        except:
            SupportsResponseEnum = SupportsResponse.NONE
        self.homeassistant.services.async_register(DOMAIN, service, service_func, supports_response=SupportsResponseEnum)

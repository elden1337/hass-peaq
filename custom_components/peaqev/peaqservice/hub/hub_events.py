import logging

from peaqevcore.common.models.observer_types import ObserverTypes

events = [
    "peaqhvac.try_heat_water_changed",    
    "peaqhvac.pre_heating_changed",
    "peaqhvac.upcoming_water_heater_warning"
]

_LOGGER = logging.getLogger(__name__)

class HubEvents:
    def __init__(self, hub, state_machine):
        self._hub = hub
        self.state_machine = state_machine
        self._aux_stop = False        
        self._event_handler_dict: dict = {}
        for e in events:
            self._event_handler_dict[e] = False
            self.state_machine.bus.async_listen(e, self.handle_event)
            _LOGGER.debug(f"Listening to {e} for aux_stop")

    def handle_event(self, event):
        ret = bool(event.data.get("new", False))
        new_state = self._aux_stop
        if ret != self._event_handler_dict[event.event_type]:
            new_state = any([self._event_handler_dict.values() == True])
        if new_state != self._aux_stop:
            _LOGGER.debug(f"Received event {event.event_type} with data {event.data}. This changed aux stop to {self._aux_stop}")
            self._aux_stop = new_state
            self._hub.observer.broadcast(ObserverTypes.AuxStopChanged)

    @property
    def aux_stop(self) -> bool:
        """Auxiliary stop of charging. Responds to various events from peaqhvac and possibly others."""
        return self._aux_stop   
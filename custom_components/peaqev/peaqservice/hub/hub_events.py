import logging

events = [
    "peaqhvac.try_heat_water_changed",
    "peaqhvac.currently_heating_changed",
    "peaqhvac.boost_changed",
    "peaqhvac.pre_heating_changed",
    "peaqhvac.upcoming_water_heater_warning"
]

_LOGGER = logging.getLogger(__name__)

class HubEvents:
    def __init__(self, hub, state_machine):
        self._hub = hub
        self.state_machine = state_machine
        self._aux_stop = False
        for e in events:
            self.state_machine.bus.async_listen(e, self.handle_event)
            _LOGGER.debug(f"Listening to {e} for aux_stop")

    def handle_event(self, event):
        _LOGGER.debug(f"Received event {event.event_type}")
        ret = bool(event.data.get("new", False))
        if ret != self._aux_stop:
            self._aux_stop = ret
            self._hub.observer.broadcast("aux stop")

    @property
    def aux_stop(self) -> bool:
        """Auxiliary stop of charging. Responds to various events from peaqhvac and possibly others."""
        return self._aux_stop
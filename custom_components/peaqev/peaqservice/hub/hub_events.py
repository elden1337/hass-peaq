import logging

from peaqevcore.common.models.observer_types import ObserverTypes

EVENTS = [
    'peaqhvac.try_heat_water_changed',
    'peaqhvac.pre_heating_changed',
    'peaqhvac.water_heater_warning'
]

_LOGGER = logging.getLogger(__name__)

class HubEvents:
    def __init__(self, state_machine, observer):
        self.state_machine = state_machine
        self.observer = observer
        self._aux_stop = False
        self._event_handler_dict: dict = {}
        for e in EVENTS:
            self._event_handler_dict[e] = False
            self.state_machine.bus.async_listen(e, self.async_handle_event)
            _LOGGER.debug('Listening to %s for aux_stop', e)

    async def async_handle_event(self, event):
        ret = bool(event.data.get('new', False))
        new_state = self._aux_stop
        if ret != self._event_handler_dict[event.event_type]:
            new_state = any([self._event_handler_dict.values() == ret])
        if new_state != self._aux_stop:
            _LOGGER.debug(
                'Received event %s with data %s. This changed aux stop to %s',
                event.event_type,
                event.data,
                self._aux_stop
            )
            self._aux_stop = new_state
            await self.observer.async_broadcast(ObserverTypes.AuxStopChanged)

    @property
    def aux_stop(self) -> bool:
        """
        Auxiliary stop of charging.
        Responds to various events from peaqhvac and possibly others.
        """
        return self._aux_stop

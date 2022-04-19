import logging

from custom_components.peaqev.peaqservice.util.constants import (
    DOMAIN,
    ON,
    OFF,
    RESUME,
    PAUSE,
    PARAMS,
    UPDATECURRENT,
)

_LOGGER = logging.getLogger(__name__)


class ServiceCalls:
    def __init__(
            self,
            domain: str,
            on_call: str,
            off_call: str,
            pause_call: str = None,
            resume_call: str = None,
            allowupdatecurrent: bool = False,
            update_current_call: str = None,
            update_current_params: dict = None,
    ):
        self._domain = domain
        self._allowupdatecurrent = allowupdatecurrent
        self._on = on_call
        self._off = off_call
        self._pause = pause_call if pause_call is not None else off_call
        self._resume = resume_call if resume_call is not None else on_call
        self._update_current = UpdateCurrent(update_current_call, update_current_params)
        self._validate_servicecalls()

    @property
    def allowupdatecurrent(self) -> bool:
        return self._allowupdatecurrent

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def on(self) -> str:
        return self._on

    @property
    def off(self) -> str:
        return self._off

    @property
    def pause(self) -> str:
        return self._pause

    @property
    def resume(self) -> str:
        return self._resume

    @property
    def update_current(self):
        return self._update_current

    def get_call(self, call) -> dict:
        ret = {}
        ret[DOMAIN] = self.domain
        ret[call] = self._get_call_type(call)
        if call is UPDATECURRENT:
            ret[PARAMS] = self.update_current.params
        return ret

    def _get_call_type(self, call):
        _callsdict = {
            ON: self.on,
            OFF: self.off,
            PAUSE: self.pause,
            RESUME: self.resume,
            UPDATECURRENT: self.update_current.call
        }
        return _callsdict.get(call)

    def _validate_servicecalls(self):
        assertions = [self.domain, self.on, self.off, self.pause, self.resume]
        try:
            for a in assertions:
                assert len(a) > 0
        except Exception as e:
            _LOGGER.error("Peaqev could not initialize servicecalls", e)


class UpdateCurrent:
    def __init__(self, call: str, params: dict):
        self._call = call
        self._params = params

    @property
    def call(self) -> str:
        return self._call

    @property
    def params(self) -> dict:
        return self._params


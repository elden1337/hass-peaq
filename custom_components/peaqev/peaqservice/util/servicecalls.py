
ON = "on"
OFF = "off"
PAUSE = "pause"
RESUME = "resume"
DOMAIN = "domain"
UPDATECURRENT = "updatecurrent"
NAME = "name"
PARAMS = "params"
CHARGER = "charger"
CHARGERID = "chargerid"
CURRENT = "current"

class ServiceCalls:
    def __init__(
            self,
            domain: str,
            on_call: str,
            off_call: str,
            pause_call: str = None,
            resume_call: str = None,
            update_current_call: str = None,
            update_current_params: dict = None
    ):
        self._domain = domain
        self._on = on_call
        self._off = off_call
        self._pause = pause_call if pause_call is not None else off_call
        self._resume = resume_call if resume_call is not None else on_call
        self._update_current = UpdateCurrent(update_current_call, update_current_params)
        self._test_servicecalls()

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

    def _get_call_type(self, call):
        _callsdict = {
            ON: self.on,
            OFF: self.off,
            PAUSE: self.pause,
            RESUME: self.resume,
            UPDATECURRENT: self.update_current.call
        }
        return _callsdict.get(call)

    def get_call(self, call) -> dict:
        ret = {}
        ret[DOMAIN] = self.domain
        ret[call] = self._get_call_type(call)
        if call is UPDATECURRENT:
            ret[PARAMS] = self.update_current.params
        return ret

    def _test_servicecalls(self):
        assertions = [self.domain, self.on, self.off, self.pause, self.resume]
        for a in assertions:
            assert len(a) > 0


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


#-----------tests----------------

servicecall_params = {}
servicecall_params[CHARGER] = "chargepoint"
servicecall_params[CHARGERID] = 2345
#servicecall_params[CHARGERID] = self._chargerid
servicecall_params[CURRENT] = "max_current"

s = ServiceCalls(
            domain="chargeamps",
            on_call="enable",
            off_call="disable",
            update_current_call="set_max_current",
            update_current_params=servicecall_params
)

print(s.domain)
print(s.on)
print(s.off)
print(s.resume)
print(s.pause)
print(s.update_current.call)
print(s.update_current.params)
print("callstests")
print(s.get_call(UPDATECURRENT))

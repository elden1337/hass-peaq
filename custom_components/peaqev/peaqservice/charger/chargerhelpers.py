import time
from datetime import datetime

from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    PARAMS,
    CURRENT,
    CHARGERID
)


class ChargerHelpers:
    def __init__(self, charger):
        self._charger = charger

    async def setchargerparams(self, calls, ampoverride:int = 0) -> dict:
        amps = ampoverride if ampoverride >= 6 else self._charger._hub.threshold.allowedcurrent
        serviceparams = {}
        if await self._checkchargerparams(calls) is True:
            serviceparams[calls[PARAMS][CHARGER]] = calls[PARAMS][CHARGERID]
        serviceparams[calls[PARAMS][CURRENT]] = amps
        return serviceparams

    def wait_turn_on(self) -> bool:
        while not self._charger._charger_is_active and self._charger.params.running:
            time.sleep(3)
        return self._updates_should_continue()

    def wait_update_current(self) -> bool:
        self._charger._hub.sensors.chargerobject_switch.updatecurrent()
        while (self._current_is_equal() or self._too_late_to_change()) and self._charger.params.running:
            time.sleep(3)
        return self._updates_should_continue()

    def wait_loop_cycle(self):
        timer = 120
        start_time = time.time()
        self._charger._hub.sensors.chargerobject_switch.updatecurrent()
        while time.time() - start_time < timer:
            time.sleep(3)
        self._charger._hub.sensors.chargerobject_switch.updatecurrent()

    def _updates_should_continue(self) -> bool:
        ret = [
            self._charger.params.running is False,
            self._charger.params.disable_current_updates
        ]
        return not any(ret)

    async def _checkchargerparams(self, calls) -> bool:
        return len(calls[PARAMS][CHARGER]) > 0 and len(calls[PARAMS][CHARGERID]) > 0

    def _current_is_equal(self) -> bool:
        return self._charger._hub.sensors.chargerobject_switch.current == self._charger._hub.threshold.allowedcurrent

    def _too_late_to_change(self) -> bool:
        return datetime.now().minute >= 55 and self._charger._hub.threshold.allowedcurrent > self._charger._hub.sensors.chargerobject_switch.current

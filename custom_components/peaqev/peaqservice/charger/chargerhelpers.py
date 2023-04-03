import time
from datetime import datetime

from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    PARAMS,
    CURRENT,
    CHARGERID
)


async def _checkchargerparams(calls) -> bool:
    return len(calls[PARAMS][CHARGER]) > 0 and len(calls[PARAMS][CHARGERID]) > 0


async def async_set_chargerparams(calls, amps: int) -> dict:
    serviceparams = {}
    if await _checkchargerparams(calls):
        serviceparams[calls[PARAMS][CHARGER]] = calls[PARAMS][CHARGERID]
    serviceparams[calls[PARAMS][CURRENT]] = amps
    return serviceparams


LOOP_WAIT = 3
TIMER = 120

class ChargerHelpers:
    def __init__(self, charger):
        self.c = charger

    def wait_turn_on(self) -> bool:
        while not self.c.charger_active and self.c.params.running:
            time.sleep(LOOP_WAIT)
        return self._updates_should_continue()

    def wait_update_current(self) -> bool:
        self.c.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition
        while all([
            (self._currents_match() or self._too_late_to_increase()),
            self.c.params.running
        ]):
            time.sleep(LOOP_WAIT)
        return self._updates_should_continue()

    def wait_loop_cycle(self):
        start_time = time.time()
        self.c.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition
        while time.time() - start_time < TIMER:
            time.sleep(LOOP_WAIT)
        self.c.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition

    def _updates_should_continue(self) -> bool:
        return not any([
            self.c.params.running is False,
            self.c.params.disable_current_updates
        ])

    def _currents_match(self) -> bool:
        return self.c.hub.sensors.chargerobject_switch.current == self.c.hub.threshold.allowedcurrent  # todo: composition

    def _too_late_to_increase(self) -> bool:
        return datetime.now().minute >= 55 and self.c.hub.threshold.allowedcurrent > self.c.hub.sensors.chargerobject_switch.current  # todo: composition

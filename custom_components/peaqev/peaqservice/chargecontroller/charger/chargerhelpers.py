import time
from datetime import datetime

from custom_components.peaqev.peaqservice.chargecontroller.charger.const import (
    LOOP_RELEASE_TIMER,
    LOOP_WAIT,
)
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGER,
    CHARGERID,
    CURRENT,
    PARAMS,
)


async def _checkchargerparams(calls) -> bool:
    return len(calls[PARAMS][CHARGER]) > 0 and len(calls[PARAMS][CHARGERID]) > 0


async def async_set_chargerparams(calls, amps: int) -> dict:
    serviceparams = {}
    if await _checkchargerparams(calls):
        serviceparams[calls[PARAMS][CHARGER]] = calls[PARAMS][CHARGERID]
    serviceparams[calls[PARAMS][CURRENT]] = amps
    return serviceparams


class ChargerHelpers:
    def __init__(self, charger):
        self.charger = charger

    # async def async_wait_turn_on(self) -> bool:
    #     while not self.charger.charger_active and self.charger.model.running:
    #         time.sleep(LOOP_WAIT)
    #     return await self.async_updates_should_continue()
    #
    # async def async_wait_update_current(self) -> bool:
    #     await self.charger.controller.hub.sensors.chargerobject_switch.async_updatecurrent()  # todo: composition
    #     while all(
    #             [
    #                 (
    #                         await self.async_currents_match()
    #                         or await self.async_too_late_to_increase()
    #                 ),
    #                 self.charger.model.running,
    #             ]
    #     ):
    #         time.sleep(LOOP_WAIT)
    #     return await self.async_updates_should_continue()
    #
    # async def async_wait_loop_cycle(self):
    #     start_time = time.time()
    #     await self.charger.controller.hub.sensors.chargerobject_switch.async_updatecurrent()  # todo: composition
    #     while time.time() - start_time < LOOP_RELEASE_TIMER:
    #         time.sleep(LOOP_WAIT)
    #     await self.charger.controller.hub.sensors.chargerobject_switch.async_updatecurrent()  # todo: composition

    # async def async_updates_should_continue(self) -> bool:
    #     return not any(
    #         [
    #             self.charger.model.running is False,
    #             self.charger.model.disable_current_updates,
    #         ]
    #     )
    #
    # async def async_currents_match(self) -> bool:
    #     return (
    #         self.charger.controller.hub.sensors.chargerobject_switch.current
    #         == await self.charger.controller.hub.threshold.async_allowed_current()
    #     )  # todo: composition
    #
    # async def async_too_late_to_increase(self) -> bool:
    #     return (
    #         datetime.now().minute >= 55
    #         and await self.charger.controller.hub.threshold.async_allowed_current()
    #         > self.charger.controller.hub.sensors.chargerobject_switch.current
    #     )  # todo: composition

    def wait_turn_on(self) -> bool:
        while not self.charger.charger_active and self.charger.model.running:
            time.sleep(LOOP_WAIT)
        return self._updates_should_continue()

    def wait_update_current(self) -> bool:
        self.charger.controller.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition
        while all(
            [
                (self._currents_match() or self._too_late_to_increase()),
                self.charger.model.running,
            ]
        ):
            time.sleep(LOOP_WAIT)
        return self._updates_should_continue()

    def wait_loop_cycle(self):
        start_time = time.time()
        self.charger.controller.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition
        while time.time() - start_time < LOOP_RELEASE_TIMER:
            time.sleep(LOOP_WAIT)
        self.charger.controller.hub.sensors.chargerobject_switch.updatecurrent()  # todo: composition

    def _updates_should_continue(self) -> bool:
        return not any(
            [
                self.charger.model.running is False,
                self.charger.model.disable_current_updates,
            ]
        )

    def _currents_match(self) -> bool:
        return (
            self.charger.controller.hub.sensors.chargerobject_switch.current
            == self.charger.controller.hub.threshold.allowed_current()
        )  # todo: composition

    def _too_late_to_increase(self) -> bool:
        return (
            datetime.now().minute >= 55
            and self.charger.controller.hub.threshold.allowed_current()
            > self.charger.controller.hub.sensors.chargerobject_switch.current
        )  # todo: composition

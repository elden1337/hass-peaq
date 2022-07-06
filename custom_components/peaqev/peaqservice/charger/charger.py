import logging
import time
from datetime import datetime

from peaqevcore.models.chargerstates import CHARGERSTATES

from custom_components.peaqev.peaqservice.charger.session import Session
from custom_components.peaqev.peaqservice.util.constants import (
    DOMAIN,
    ON,
    OFF,
    RESUME,
    PAUSE,
    CHARGER,
    PARAMS,
    UPDATECURRENT,
    CURRENT,
    CHARGERID
)

_LOGGER = logging.getLogger(__name__)
CALL_WAIT_TIMER = 60

class Charger:
    def __init__(self, hub, hass, servicecalls):
        self._hass = hass
        self._hub = hub
        self._charger_running = False
        self._charger_stopped = False
        self._service_calls = servicecalls
        self._session_is_active = False
        self._latest_charger_call = 0
        self._repeat_is_running = False
        self.session = Session(self)

    @property
    def _chargertype_charger_is_on(self) -> bool:
        if self._hub.chargertype.charger.options.powerswitch_controls_charging:
            return self._hub.chargerobject_switch.value
        return all(
            [
                self._hub.chargerobject_switch.value,
                self._hub.carpowersensor.value > 0
            ]
        )

    @property
    def session_is_active(self) -> bool:
        return self._session_is_active

    @session_is_active.setter
    def session_is_active(self, val):
        self._session_is_active = val

    async def charge(self):
        """Main function to turn charging on or off"""
        if self._repeat_is_running:
            await self._is_running(False)
        if self._hub.charger_enabled.value is True:
            self.session_is_active = True
            if self._hub.chargecontroller.status is CHARGERSTATES.Start.name:
                if self._chargertype_charger_is_on is False and self._charger_running is False:
                    await self._start_charger()
            elif self._hub.chargecontroller.status in [CHARGERSTATES.Stop.name, CHARGERSTATES.Idle.name]:
                if (self._chargertype_charger_is_on or self._hub.carpowersensor.value > 0) is True and self._charger_stopped is False:
                    await self._pause_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Done.name and self._hub.charger_done.value is False:
                await self._terminate_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Idle.name:
                self._hub.charger_done.value = False
                if self._chargertype_charger_is_on is True:
                    await self._terminate_charger()
        else:
            if self._chargertype_charger_is_on is True and self._charger_stopped is False:
                await self._terminate_charger()
            return

    async def _start_charger(self):
        if time.time() - self._latest_charger_call > CALL_WAIT_TIMER:
            await self._is_running(True)
            if self._session_is_active is False:
                await self._call_charger(ON)
                self._session_is_active = True
            else:
                await self._call_charger(RESUME)
            self._hub.chargecontroller.update_latestchargerstart()
            if self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent is True and self._hub.locale.data.free_charge(self._hub.locale.data) is False:
                self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self):
        if time.time() - self._latest_charger_call > CALL_WAIT_TIMER:
            self.session_is_active = False
            await self._is_running(False)
            self._session_is_active = False
            await self._call_charger(OFF)
            self._hub.charger_done.value = True

    async def _pause_charger(self):
        if time.time() - self._latest_charger_call > CALL_WAIT_TIMER:
            await self._is_running(False)
            if self._hub.charger_done.value is True or self._hub.chargecontroller.status is CHARGERSTATES.Idle:
                await self._terminate_charger()
            else:
                await self._call_charger(PAUSE)

    async def _call_charger(self, command: str):
        calls = self._service_calls.get_call(command)
        await self._hub.hass.services.async_call(
            calls[DOMAIN],
            calls[command],
            calls["params"]
        )
        msg = f"Calling charger {command}"
        _LOGGER.debug(msg)
        self._latest_charger_call = time.time()

    async def _updatemaxcurrent(self):
        """If enabled, let the charger periodically update it's current during charging."""
        self._hub.chargerobject_switch.updatecurrent()
        calls = self._service_calls.get_call(UPDATECURRENT)
        if await self._hass.async_add_executor_job(self._wait_turn_on):
            #call here to set amp-list
            while self._hub.chargerobject_switch.value is True and self._charger_running is True:
                if await self._hass.async_add_executor_job(self._wait_update_current):
                    serviceparams = await self._setchargerparams(calls)
                    _LOGGER.debug(f"peaqev updating current with: {calls[DOMAIN]}, {calls[UPDATECURRENT]} and params: {serviceparams}")
                    await self._hub.hass.services.async_call(
                        calls[DOMAIN],
                        calls[UPDATECURRENT],
                        serviceparams
                    )
                    await self._hass.async_add_executor_job(self._wait_loop_cycle)

            if self._hub.chargertype.charger.servicecalls.options.update_current_on_termination:
                final_service_params = await self._setchargerparams(calls, ampoverride=6)
                await self._hub.hass.services.async_call(
                    calls[DOMAIN],
                    calls[UPDATECURRENT],
                    final_service_params
                )

    async def _setchargerparams(self, calls, ampoverride:int = 0) -> dict:
        amps = ampoverride if ampoverride >= 6 else self._hub.threshold.allowedcurrent
        serviceparams = {}
        if await self._checkchargerparams(calls) is True:
            serviceparams[calls[PARAMS][CHARGER]] = calls[PARAMS][CHARGERID]
        serviceparams[calls[PARAMS][CURRENT]] = amps
        return serviceparams

    async def _checkchargerparams(self, calls) -> bool:
        return len(calls[PARAMS][CHARGER]) > 0 and len(calls[PARAMS][CHARGERID]) > 0

    def _wait_turn_on(self) -> bool:
        while self._chargertype_charger_is_on is False and self._charger_stopped is False:
            time.sleep(3)
        if self._charger_stopped is True:
            return False
        return True

    def _wait_update_current(self) -> bool:
        self._hub.chargerobject_switch.updatecurrent()
        while (self._hub.chargerobject_switch.current == self._hub.threshold.allowedcurrent
               or (datetime.now().minute >= 55
                   and self._hub.threshold.allowedcurrent > self._hub.chargerobject_switch.current)) \
                and self._charger_stopped is False:
            time.sleep(3)
        if self._charger_stopped is True:
            return False
        return True

    def _wait_loop_cycle(self):
        timer = 180
        start_time = time.time()
        self._hub.chargerobject_switch.updatecurrent()
        while time.time() - start_time < timer:
            time.sleep(3)
        self._hub.chargerobject_switch.updatecurrent()

    async def _is_running(self, determinator: bool):
        if determinator:
            self._charger_running = True
            self._charger_stopped = False
            _LOGGER.debug("charger-class has been started")
        elif not determinator:
            charger = self._hub.chargerobject.value.lower()
            chargingstates = self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]
            if charger not in chargingstates:
                self._charger_running = False
                self._charger_stopped = True
                self._repeat_is_running = False
                _LOGGER.debug("charger-class has been stopped")
            else:
                self._repeat_is_running = True

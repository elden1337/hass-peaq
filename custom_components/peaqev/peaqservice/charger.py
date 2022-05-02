import logging
import time
from datetime import datetime

from peaqevcore.Models import CHARGERSTATES
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


class Charger:
    def __init__(self, hub, hass, servicecalls):
        self._hass = hass
        self._hub = hub
        self._charger_running = False
        self._charger_stopped = False
        self._service_calls = servicecalls
        self._session_is_active = False

    async def charge(self):
        """Main function to turn charging on or off"""
        if self._hub.charger_enabled.value is True:
            if self._hub.chargecontroller.status is CHARGERSTATES.Start:
                if self._hub.chargerobject_switch.value is False and self._charger_running is False:
                    await self._start_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Stop or self._hub.chargecontroller.status is CHARGERSTATES.Idle:
                if self._hub.chargerobject_switch.value is True and self._charger_stopped is False:
                    await self._pause_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Done and self._hub.charger_done.value is False:
                await self._terminate_charger()
        else:
            if self._hub.chargerobject_switch.value is True and self._charger_stopped is False:
                await self._terminate_charger()

    async def _start_charger(self):
        self._is_running(True)
        if self._session_is_active is False:
            await self._call_charger(ON)
            self._session_is_active = True
        else:
            await self._call_charger(RESUME)
        self._hub.chargecontroller.update_latestchargerstart()
        if self._hub.chargertype.charger.servicecalls.allowupdatecurrent is True and self._hub.locale.data.free_charge is False:
            self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self):
        self._is_running(False)
        self._session_is_active = False
        await self._call_charger(OFF)
        self._hub.charger_done.value = True

    async def _pause_charger(self):
        self._is_running(False)
        if self._hub.charger_done.value is True or self._hub.chargecontroller.status is CHARGERSTATES.Idle:
            await self._terminate_charger()
        else:
            await self._call_charger(PAUSE)

    async def _call_charger(self, command: str):
        msg = f"Calling charger {command}"
        _LOGGER.info(msg)
        calls = self._service_calls.get_call(command)

        await self._hub.hass.services.async_call(
            calls[DOMAIN],
            calls[command],
            calls["params"]
        )

    async def _updatemaxcurrent(self):
        """If enabled, let the charger periodically update it's current during charging."""
        self._hub.chargerobject_switch.updatecurrent()
        calls = self._service_calls.get_call(UPDATECURRENT)

        if await self._hass.async_add_executor_job(self._wait_turn_on):
            #call here to set amp-list
            while self._hub.chargerobject_switch.value is True and self._charger_running is True:
                if await self._hass.async_add_executor_job(self._wait_update_current):
                    serviceparams = await self._setchargerparams(calls)
                    info = f"peaqev updating current with: {calls[DOMAIN]}, {calls[UPDATECURRENT]} and params: {serviceparams}"
                    _LOGGER.info(info)
                    await self._hub.hass.services.async_call(
                        calls[DOMAIN],
                        calls[UPDATECURRENT],
                        serviceparams
                    )
                    await self._hass.async_add_executor_job(self._wait_loop_cycle)

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
        while self._hub.chargerobject_switch.value is False and self._charger_stopped is False:
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

    def _is_running(self, determinator: bool):
        if determinator:
            self._charger_running = True
            self._charger_stopped = False
        elif not determinator:
            self._charger_running = False
            self._charger_stopped = True

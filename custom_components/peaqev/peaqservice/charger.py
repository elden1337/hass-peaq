import time
import logging
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
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
        self._chargerrunning = False
        self._chargerstopped = False
        self._service_calls = servicecalls
        self._sessionrunning = False

    async def charge(self):
        """Main function to turn charging on or off"""
        if self._hub.charger_enabled.value is True:
            if self._hub.chargecontroller.status is CHARGECONTROLLER.Start:
                if self._hub.chargerobject_switch.value == "off" and self._chargerrunning is False:
                    await self._start_charger()
            elif self._hub.chargecontroller.status is CHARGECONTROLLER.Stop or self._hub.chargecontroller.status is CHARGECONTROLLER.Idle:
                if self._hub.chargerobject_switch.value == "on" and self._chargerstopped is False:
                    await self._pause_charger()
            elif self._hub.chargecontroller.status is CHARGECONTROLLER.Done and self._hub.charger_done.value is False:
                await self._terminate_charger()
        else:
            if self._hub.chargerobject_switch.value == "on" and self._chargerstopped is False:
                await self._terminate_charger()

    async def _start_charger(self):
        self._is_running(True)
        if self._sessionrunning is False:
            await self._call_charger(ON)
            self._sessionrunning = True
        else:
            await self._call_charger(RESUME)
        self._hub.chargecontroller.update_latestchargerstart()
        if self._hub.chargertypedata.charger.servicecalls.allowupdatecurrent is True:
            _LOGGER.info("peaqev init updatemaxcurrent")
            self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self):
        self._is_running(False)
        self._sessionrunning = False
        await self._call_charger(OFF)
        self._hub.charger_done.value = True

    async def _pause_charger(self):
        self._is_running(False)
        if self._hub.charger_done.value is True or self._hub.chargecontroller.status is CHARGECONTROLLER.Idle:
            await self._terminate_charger()
        else:
            await self._call_charger(PAUSE)

    async def _call_charger(self, command: str):
        calls = self._service_calls.get_call(command)
        await self._hub.hass.services.async_call(
            calls[DOMAIN],
            calls[command]
        )

    async def _updatemaxcurrent(self):
        """If enabled, let the charger periodically update it's current during charging."""

        calls = self._service_calls.get_call(UPDATECURRENT)
        await self._hass.async_add_executor_job(self._wait_turn_on)

        while self._hub.chargerobject_switch.value == "on" and self._chargerstopped is False:
            await self._hass.async_add_executor_job(self._wait_update_current)

            if self._chargerrunning is True and self._chargerstopped is False:
                serviceparams = await self._setchargerparams(calls)
                info = f"peaqev updating charging current with: {calls[DOMAIN]}, {calls[UPDATECURRENT]} and params: {serviceparams}"
                _LOGGER.info(info)
                await self._hub.hass.services.async_call(
                    calls[DOMAIN],
                    calls[UPDATECURRENT],
                    serviceparams
                )
                await self._hass.async_add_executor_job(self._wait_loop_cycle)

        finalserviceparams = await self._setchargerparams(calls, ampoverride=6)
        await self._hub.hass.services.async_call(
            calls[DOMAIN],
            calls[UPDATECURRENT],
            finalserviceparams
        )

    async def _setchargerparams(self, calls:dict, ampoverride:int = 0):
        amps = ampoverride if ampoverride >= 6 else self._hub.threshold.allowedcurrent
        if await self._checkchargerparams(calls) is True:
            serviceparams = {
                calls[PARAMS][CHARGER]: calls[UPDATECURRENT][PARAMS][CHARGERID],
                calls[PARAMS][CURRENT]: amps
            }
        else:
            serviceparams = {
                calls[PARAMS][CURRENT]: amps
            }
        return serviceparams

    async def _checkchargerparams(self, calls:dict) -> bool:
        return len(calls[PARAMS][CHARGER]) > 0 and len(calls[PARAMS][CHARGERID]) > 0

    def _wait_turn_on(self) -> None:
        while self._hub.chargerobject_switch.value == "off" and self._chargerstopped is False:
            time.sleep(3)

    def _wait_update_current(self) -> None:
        while (int(self._hub.chargerobject_switch.current) == int(self._hub.threshold.allowedcurrent) and self._chargerstopped is False):
            #or (datetime.now().minute >= 55 and allowed_current > switch_current and self._chargerstopped is False):
            time.sleep(3)

    def _wait_loop_cycle(self) -> None:
        timer = 180
        starttime = time.time()
        while time.time() - starttime < timer:
            time.sleep(3)

    def _is_running(self, determinator: bool):
        if determinator:
            self._chargerrunning = True
            self._chargerstopped = False
        elif not determinator:
            self._chargerrunning = False
            self._chargerstopped = True

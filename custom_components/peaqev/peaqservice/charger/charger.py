import logging
import time

from peaqevcore.models.chargerstates import CHARGERSTATES
from peaqevcore.services.session.session import Session

from custom_components.peaqev.peaqservice.charger.chargerhelpers import ChargerHelpers
from custom_components.peaqev.peaqservice.charger.chargerparams import ChargerParams
from custom_components.peaqev.peaqservice.util.constants import (
    DOMAIN,
    ON,
    OFF,
    RESUME,
    PAUSE,
    UPDATECURRENT
)

_LOGGER = logging.getLogger(__name__)
CALL_WAIT_TIMER = 60

from enum import Enum

class ChargerStateEnum(Enum):
    Stop = 0
    Start = 1
    Pause = 2
    Resume = 3


class Charger:
    def __init__(self, hub, hass, servicecalls):
        self._hass = hass
        self._hub = hub
        self._service_calls = servicecalls
        self._params = ChargerParams()
        self.session = Session(self)
        self.helpers = ChargerHelpers(self)

    @property
    def session_active(self) -> bool:
        return self._params.session_active

    @session_active.setter
    def session_active(self, val):
        self._params.session_active = val

    async def charge(self):
        """Main function to turn charging on or off"""
        if self._params.charger_state_mismatch:
            await self._update_charger_state_internal(ChargerStateEnum.Pause)
        if self._hub.sensors.charger_enabled.value and not self._hub.sensors.power.killswitch.is_dead:
            if not self.session_active and self._hub.chargecontroller.status != CHARGERSTATES.Done.name:
                _LOGGER.debug("There was no session active, so I created one.")
                self.session.core.reset()
                self.session_active = True
            if self._hub.chargecontroller.status is CHARGERSTATES.Start.name:
                if not self._params.running:
                    if not self._charger_is_active:
                        await self._start_charger()
                    else:
                        _LOGGER.debug("Detected charger running outside of peaqev-session, overtaking command.")
                        await self._overtake_charger()
            elif self._hub.chargecontroller.status in [CHARGERSTATES.Stop.name, CHARGERSTATES.Idle.name]:
                if self._charger_is_active:
                    if self._params.stopped and not self.session_active:
                        _LOGGER.debug("Detected charger running outside of peaqev-session, overtaking command and pausing.")
                    await self._pause_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Done.name and not self._hub.sensors.charger_done.value:
                _LOGGER.debug("Going to terminate since the charger is done.")
                await self._terminate_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Idle.name:
                self._hub.sensors.charger_done.value = False
                if self._charger_is_active:
                    await self._terminate_charger()
        else:
            if self._charger_is_active and not self._params.stopped:
                if self._hub.sensors.power.killswitch.is_dead:
                    _LOGGER.error(f"Your powersensor has failed to update peaqev for more than {self._hub.sensors.power.killswitch.total_timer} seconds. Therefore charging is paused until it comes alive again.")
                    await self._pause_charger()
                else:
                    _LOGGER.debug(f"I'm here even though i Shouldn't be. Executing Terminate_charger to be sure.")
                    await self._terminate_charger()
            return

    @property
    def _charger_is_active(self) -> bool:
        if self._hub.chargertype.charger.options.powerswitch_controls_charging:
            return self._hub.sensors.chargerobject_switch.value
        return all(
            [
                self._hub.sensors.chargerobject_switch.value,
                self._hub.sensors.carpowersensor.value > 0
            ]
        )

    async def _overtake_charger(self):
        await self._update_charger_state_internal(ChargerStateEnum.Start)
        self.session_active = True
        self._hub.chargecontroller.update_latestchargerstart()
        if self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent and not self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data):
            self._hass.async_create_task(self._updatemaxcurrent())

    async def _start_charger(self):
        if time.time() - self._params.latest_charger_call > CALL_WAIT_TIMER and not self._hub.sensors.power.killswitch.is_dead:
            await self._update_charger_state_internal(ChargerStateEnum.Start)
            if not self.session_active:
                await self._call_charger(ON)
                self.session_active = True
            else:
                await self._call_charger(RESUME)
            self._hub.chargecontroller.update_latestchargerstart()
            if self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent and not self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data):
                self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self):
        if time.time() - self._params.latest_charger_call > CALL_WAIT_TIMER:
            await self._hass.async_add_executor_job(self.session.core.terminate)
            await self._update_charger_state_internal(ChargerStateEnum.Stop)
            self.session_active = False
            await self._call_charger(OFF)
            self._hub.sensors.charger_done.value = True

    async def _pause_charger(self):
        if time.time() - self._params.latest_charger_call > CALL_WAIT_TIMER:
            if self._hub.sensors.charger_done.value is True or self._hub.chargecontroller.status is CHARGERSTATES.Idle:
                await self._terminate_charger()
            else:
                await self._call_charger(PAUSE)
                await self._update_charger_state_internal(ChargerStateEnum.Pause)

    async def _call_charger(self, command: str):
        calls = self._service_calls.get_call(command)
        if self._hub.chargertype.charger.servicecalls.options.switch_controls_charger:
            await self._hub.state_machine.states.async_set(self._hub.chargertype.charger.entities.powerswitch, calls[command])
            _LOGGER.debug(f"Calling charger-outlet")
        else:
            await self._do_service_call(calls[DOMAIN], calls[command], calls["params"])
        self._params.latest_charger_call = time.time()

    async def _updatemaxcurrent(self):
        self._hub.sensors.chargerobject_switch.updatecurrent()
        calls = self._service_calls.get_call(UPDATECURRENT)
        if await self._hass.async_add_executor_job(self.helpers.wait_turn_on):
            #call here to set amp-list
            while self._hub.sensors.chargerobject_switch.value is True and self._params.running is True:
                if await self._hass.async_add_executor_job(self.helpers.wait_update_current):
                    serviceparams = await self.helpers.setchargerparams(calls)
                    if not self._params.disable_current_updates:
                        await self._do_service_call(calls[DOMAIN], calls[UPDATECURRENT], serviceparams)
                    await self._hass.async_add_executor_job(self.helpers.wait_loop_cycle)

            if self._hub.chargertype.charger.servicecalls.options.update_current_on_termination is True:
                final_service_params = await self.helpers.setchargerparams(calls, ampoverride=6)
                await self._do_service_call(calls[DOMAIN], calls[UPDATECURRENT], final_service_params)

    async def _do_service_call(self, domain, command, params):
        _LOGGER.debug(f"Calling charger {command} for domain '{domain}' with parameters: {params}")
        await self._hub.state_machine.services.async_call(
            domain,
            command,
            params
        )

    async def _update_charger_state_internal(self, state: ChargerStateEnum):
        if state in [ChargerStateEnum.Start, ChargerStateEnum.Resume]:
            self._params.running = True
            self._params.stopped = False
            self._params.disable_current_updates = False
            _LOGGER.debug("Peaqev internal charger has been started")
        elif state in [ChargerStateEnum.Stop, ChargerStateEnum.Pause]:
            self._params.disable_current_updates = True
            charger_state = self._hub.sensors.chargerobject.value.lower()
            chargingstates = self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]
            if charger_state not in chargingstates or len(charger_state) < 1:
                self._params.running = False
                self._params.stopped = True
                self._params.charger_state_mismatch = False
                _LOGGER.debug("Peaqev internal charger has been stopped")
            else:
                self._params.charger_state_mismatch = True
                _LOGGER.debug(f"Tried to stop connected charger, but it's reporting: {charger_state} as state. Retrying stop-attempt.")

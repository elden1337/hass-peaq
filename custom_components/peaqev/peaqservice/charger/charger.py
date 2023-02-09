import logging
import time

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from peaqevcore.services.session.session import Session

from custom_components.peaqev.peaqservice.charger.charger_states import ChargerStates
from custom_components.peaqev.peaqservice.charger.chargerhelpers import ChargerHelpers
from custom_components.peaqev.peaqservice.charger.chargerparams import ChargerParams
from custom_components.peaqev.peaqservice.util.constants import (
    DOMAIN,
    PARAMS,
    CURRENT
)

_LOGGER = logging.getLogger(__name__)
CALL_WAIT_TIMER = 60


class Charger:
    def __init__(self, hub, hass, servicecalls):
        self._hass = hass
        self.hub = hub
        self._service_calls = servicecalls
        self.params = ChargerParams()
        self.session = Session(self)
        self.helpers = ChargerHelpers(self)

    @property
    def session_active(self) -> bool:
        return self.params.session_active

    @session_active.setter
    def session_active(self, val):
        self.params.session_active = val

    @property
    def charger_active(self) -> bool:
        if self.hub.chargertype.options.powerswitch_controls_charging:
            return self.hub.sensors.chargerobject_switch.value
        return all(
            [
                self.hub.sensors.chargerobject_switch.value,
                self.hub.sensors.carpowersensor.value > 0
            ]
        )

    async def charge(self) -> None:
        """Main function to turn charging on or off"""
        if self.params.charger_state_mismatch:
            await self._update_charger_state_internal(ChargerStates.Pause)
        if self.hub.sensors.charger_enabled.value and not self.hub.sensors.power.killswitch.is_dead:
            await self._reset_session()
            match self.hub.chargecontroller.status_type:
                case ChargeControllerStates.Start:
                    if not self.params.running:
                        await self._start_charger() if not self.charger_active else await self._overtake_charger(
                            debugmessage="Detected charger running outside of peaqev-session, overtaking command.")
                case ChargeControllerStates.Stop | ChargeControllerStates.Idle:
                    if self.charger_active:
                        await self._pause_charger(
                            debugmessage="Detected charger running outside of peaqev-session, overtaking command and pausing.") if not self.params.running and not self.session_active else None
                case ChargeControllerStates.Done:
                    if not self.hub.sensors.charger_done.value:
                        await self._terminate_charger(debugmessage="Going to terminate since the charger is done.")
                case ChargeControllerStates.Idle:
                    self.hub.sensors.charger_done.value = False
                    await self._terminate_charger() if self.charger_active else None
                case _:
                    _LOGGER.debug("Could not match any chargecontroller-state.")
        else:
            if self.charger_active and self.params.running:
                debugmsg = None
                if self.hub.sensors.power.killswitch.is_dead:
                    debugmsg = f"Your powersensor has failed to update peaqev for more than {self.hub.sensors.power.killswitch.total_timer} seconds. Therefore charging is paused until it comes alive again."
                elif self.hub.sensors.charger_enabled.value:
                    debugmsg = "Detected charger running outside of peaqev-session, overtaking command and pausing."
                await self._pause_charger(debugmessage=debugmsg)

    async def _reset_session(self) -> None:
        if not self.session_active and self.hub.chargecontroller.status_type is not ChargeControllerStates.Done:
            _LOGGER.debug("There was no session active, so I created one.")
            self.session.core.reset()
            self.session_active = True

    async def _overtake_charger(self, debugmessage: str = None):
        await self._debug_log(debugmessage)
        await self._update_charger_state_internal(ChargerStates.Start)
        self.session_active = True
        self.hub.chargecontroller.latest_charger_start = time.time()
        if self.hub.chargertype.servicecalls.options.allowupdatecurrent and not self.hub.sensors.locale.data.free_charge(
                self.hub.sensors.locale.data):
            self._hass.async_create_task(self._updatemaxcurrent())

    async def _start_charger(self, debugmessage: str = None):
        await self._debug_log(debugmessage)
        if time.time() - self.params.latest_charger_call > CALL_WAIT_TIMER and not self.hub.sensors.power.killswitch.is_dead:
            await self._update_charger_state_internal(ChargerStates.Start)
            if not self.session_active:
                await self._call_charger(CallTypes.On)
                self.session_active = True
            else:
                await self._call_charger(CallTypes.Resume)
            self.hub.chargecontroller.latest_charger_start = time.time()
            if self.hub.chargertype.servicecalls.options.allowupdatecurrent and not self.hub.sensors.locale.data.free_charge(
                    self.hub.sensors.locale.data):
                self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self, debugmessage: str = None):
        await self._debug_log(debugmessage)
        if time.time() - self.params.latest_charger_call > CALL_WAIT_TIMER:
            await self._hass.async_add_executor_job(self.session.core.terminate)
            await self._update_charger_state_internal(ChargerStates.Stop)
            self.session_active = False
            await self._call_charger(CallTypes.Off)
            self.hub.sensors.charger_done.value = True

    async def _pause_charger(self, debugmessage: str = None):
        await self._debug_log(debugmessage)
        if time.time() - self.params.latest_charger_call > CALL_WAIT_TIMER:
            if self.hub.sensors.charger_done.value is True or self.hub.chargecontroller.status_type is ChargeControllerStates.Idle:
                await self._terminate_charger()
            else:
                await self._update_charger_state_internal(ChargerStates.Pause)
                await self._call_charger(CallTypes.Pause)

    async def _call_charger(self, command: CallTypes):
        calls = self._service_calls.get_call(command)
        if self.hub.chargertype.servicecalls.options.switch_controls_charger:
            await self.hub.state_machine.states.async_set(self.hub.chargertype.entities.powerswitch,
                                                          calls[command])
            await self._debug_log(f"Calling charger-outlet")
        else:
            await self._do_service_call(calls[DOMAIN], calls[command], calls["params"])
        self.params.latest_charger_call = time.time()

    async def _updatemaxcurrent(self):
        self.hub.sensors.chargerobject_switch.updatecurrent()
        calls = self._service_calls.get_call(CallTypes.UpdateCurrent)
        if await self._hass.async_add_executor_job(self.helpers.wait_turn_on):
            # call here to set amp-list
            while self.hub.sensors.chargerobject_switch.value is True and self.params.running is True:
                if await self._hass.async_add_executor_job(self.helpers.wait_update_current):
                    serviceparams = await self.helpers.setchargerparams(calls)
                    if not self.params.disable_current_updates and self.hub.power_canary.allow_adjustment(
                            new_amps=serviceparams[calls[PARAMS][CURRENT]]):
                        await self._do_service_call(calls[DOMAIN], calls[CallTypes.UpdateCurrent], serviceparams)
                    await self._hass.async_add_executor_job(self.helpers.wait_loop_cycle)

            if self.hub.chargertype.servicecalls.options.update_current_on_termination is True:
                final_service_params = await self.helpers.setchargerparams(calls, ampoverride=6)
                await self._do_service_call(calls[DOMAIN], calls[CallTypes.UpdateCurrent], final_service_params)

    async def _do_service_call(self, domain, command, params):
        await self._debug_log(f"Calling charger {command} for domain '{domain}' with parameters: {params}")
        await self.hub.state_machine.services.async_call(
            domain,
            command,
            params
        )

    async def _update_charger_state_internal(self, state: ChargerStates):
        if state in [ChargerStates.Start, ChargerStates.Resume]:
            self.params.running = True
            self.params.disable_current_updates = False
            _LOGGER.debug("Peaqev internal charger has been started")
        elif state in [ChargerStates.Stop, ChargerStates.Pause]:
            self.params.disable_current_updates = True
            charger_state = self.hub.sensors.chargerobject.value.lower()
            chargingstates = self.hub.chargertype.chargerstates[ChargeControllerStates.Charging]
            if charger_state not in chargingstates or len(charger_state) < 1:
                self.params.running = False
                self.params.charger_state_mismatch = False
                _LOGGER.debug("Peaqev internal charger has been stopped")
            else:
                self.params.charger_state_mismatch = True
                _LOGGER.debug(
                    f"Tried to stop connected charger, but it's reporting: {charger_state} as state. Retrying stop-attempt.")

    async def _debug_log(self, debugmessage:str = None) -> None:
        if debugmessage is not None:
            _LOGGER.debug(debugmessage)

import logging
import time

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from custom_components.peaqev.peaqservice.util.extensionmethods import log_once
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from peaqevcore.services.session.session import Session

from custom_components.peaqev.peaqservice.charger.charger_states import ChargerStates
from custom_components.peaqev.peaqservice.charger.chargerhelpers import ChargerHelpers
from custom_components.peaqev.peaqservice.charger.chargerparams import ChargerParams
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import ChargerType
from custom_components.peaqev.peaqservice.util.constants import (
    DOMAIN,
    PARAMS,
    CURRENT
)

_LOGGER = logging.getLogger(__name__)
CALL_WAIT_TIMER = 60


class Charger:
    def __init__(self, hub, chargertype):
        self.hub = hub
        self._charger = chargertype
        self.params = ChargerParams()
        self.session = Session(self)
        self.helpers = ChargerHelpers(self)
        self.hub.observer.add("power canary dead", self.async_pause_charger)
        self.hub.observer.add("chargecontroller status changed", self.async_set_chargecontroller_status)

    @property
    def session_active(self) -> bool:
        return self.params.session_active

    @session_active.setter
    def session_active(self, val):
        self.params.session_active = val

    @property
    def charger_active(self) -> bool:
        if self._charger.options.powerswitch_controls_charging:
            return self.hub.sensors.chargerobject_switch.value  # todo: composition
        return all(
            [
                self.hub.sensors.chargerobject_switch.value,  # todo: composition
                self.hub.sensors.carpowersensor.value > 0  # todo: composition
            ]
        )

    async def async_set_chargecontroller_status(self, val):
        if isinstance(val, ChargeControllerStates):
            if val is not self.params.chargecontroller_state:
                self.params.chargecontroller_state = val
                await self.charge()

    async def charge(self) -> None:
        """Main function to turn charging on or off"""
        if self._charger.type is ChargerType.NoCharger:
            return
        if self.params.charger_state_mismatch:
            await self.async_update_internal_state(ChargerStates.Pause)
        if self.hub.enabled and not self.hub.sensors.power.killswitch.is_dead:
            await self.async_reset_session()
            match self.params.chargecontroller_state:
                case ChargeControllerStates.Start:
                    await self.async_start_case()
                case ChargeControllerStates.Stop:
                    await self.async_stop_case()
                case ChargeControllerStates.Done | ChargeControllerStates.Idle:
                    await self.async_done_idle_case()
                case _:
                    _LOGGER.debug(f"Could not match any chargecontroller-state. chargecontroller reports: {self.params.chargecontroller_state}")
        else:
            if self.charger_active and self.params.running:
                if self.hub.sensors.power.killswitch.is_dead:
                    _LOGGER.debug(f"Your powersensor has failed to update peaqev for more than {self.hub.sensors.power.killswitch.total_timer} seconds. Therefore charging is paused until it comes alive again.")
                elif self.hub.enabled:
                    _LOGGER.debug("Detected charger running outside of peaqev-session, overtaking command and pausing.")
                await self.async_pause_charger()

    async def async_done_idle_case(self) -> None:
        _state = self.params.chargecontroller_state
        if not self.hub.charger_done and _state is ChargeControllerStates.Done:
            _LOGGER.debug("Going to terminate since the charger is done.")
            await self.async_terminate_charger()
        elif self.charger_active and _state is ChargeControllerStates.Idle:
            _LOGGER.debug("Going to terminate since the car has been disconnected.")
            await self.async_terminate_charger()

    async def async_stop_case(self) -> None:
        if self.charger_active:
            if not self.params.running and not self.session_active:
                _LOGGER.debug("Detected charger running outside of peaqev-session, overtaking command and pausing.")
            await self.async_pause_charger()

    async def async_start_case(self) -> None:
        if not self.params.running:
            if not self.charger_active:
                await self.async_start_charger()
            else:
                _LOGGER.debug("Detected charger running outside of peaqev-session, overtaking command.")
                await self.async_overtake_charger()

    async def async_reset_session(self) -> None:
        if not self.session_active and self.params.chargecontroller_state is not ChargeControllerStates.Done:
            self.session.core.reset()
            self.session_active = True

    async def async_overtake_charger(self) -> None:
        await self.async_update_internal_state(ChargerStates.Start)
        self.session_active = True
        await self.async_post_start_charger()

    async def async_call_ok(self) -> bool:
        return time.time() - self.params.latest_charger_call > CALL_WAIT_TIMER

    async def async_start_charger(self) -> None:
        if await self.async_call_ok():
            await self.async_update_internal_state(ChargerStates.Start)
            if not self.session_active:
                await self.async_call_charger(CallTypes.On)
                self.session_active = True
            else:
                await self.async_call_charger(CallTypes.Resume)
            await self._postasync_start_charger()

    async def async_post_start_charger(self) -> None:
        await self.hub.observer.async_broadcast("update latest charger start", time.time())
        if self._charger.servicecalls.options.allowupdatecurrent and not self.hub.is_free_charge:
            self.hub.state_machine.async_create_task(self.async_update_max_current())

    async def async_terminate_charger(self) -> None:
        if await self.async_call_ok():
            await self.hub.state_machine.async_add_executor_job(self.session.core.terminate)
            await self.async_update_internal_state(ChargerStates.Stop)
            self.session_active = False
            await self.async_call_charger(CallTypes.Off)
            await self.hub.observer.async_broadcast("update charger done", True)

    async def async_pause_charger(self) -> None:
        if await self.async_call_ok():
            if self.hub.charger_done or self.params.chargecontroller_state is ChargeControllerStates.Idle:
                await self.async_terminate_charger()
            else:
                await self.async_update_internal_state(ChargerStates.Pause)
                await self.async_call_charger(CallTypes.Pause)

    async def async_call_charger(self, command: CallTypes) -> None:
        calls = self._charger.servicecalls.get_call(command)
        if self._charger.servicecalls.options.switch_controls_charger:  # todo: composition
            await self.async_do_outlet_update(calls.get(command))
        else:
            await self.async_do_service_call(calls.get(DOMAIN), calls.get(command), calls.get("params"))
        self.params.latest_charger_call = time.time()

    async def async_update_max_current(self) -> None:
        self.hub.sensors.chargerobject_switch.updatecurrent()
        calls = self._charger.servicecalls.get_call(CallTypes.UpdateCurrent)
        if await self.hub.state_machine.async_add_executor_job(self.helpers.wait_turn_on):
            # call here to set amp-list
            while all([
                self.hub.sensors.chargerobject_switch.value,
                self.params.running
            ]):
                if await self.hub.state_machine.async_add_executor_job(self.helpers.wait_update_current):
                    serviceparams = await self.helpers.setchargerparams(calls)
                    if not self.params.disable_current_updates and await self.hub.power_canary.async_allow_adjustment(
                            new_amps=serviceparams[calls[PARAMS][CURRENT]]):
                        await self.async_do_service_call(calls[DOMAIN], calls[CallTypes.UpdateCurrent], serviceparams)
                    await self.hub.state_machine.async_add_executor_job(self.helpers.wait_loop_cycle)

            if self._charger.servicecalls.options.update_current_on_termination is True:
                final_service_params = await self.helpers.setchargerparams(calls, ampoverride=6)
                await self.async_do_service_call(
                    calls[DOMAIN],
                    calls[CallTypes.UpdateCurrent],
                    final_service_params
                )

    async def async_do_outlet_update(self, call):
        _LOGGER.debug("Calling charger-outlet")
        await self.hub.state_machine.states.async_set(self._charger.entities.powerswitch, call)  # todo: composition

    async def async_do_service_call(self, domain, command, params) -> None:
        _LOGGER.debug(f"Calling charger {command} for domain '{domain}' with parameters: {params}")
        await self.hub.state_machine.services.async_call(
            domain,
            command,
            params
        )

    async def async_update_internal_state(self, state: ChargerStates) -> None:
        if state in [ChargerStates.Start, ChargerStates.Resume]:
            await self.async_update_internal_state_on()
        elif state in [ChargerStates.Stop, ChargerStates.Pause]:
            await self.async_update_internal_state_off()

    async def async_update_internal_state_on(self):
        self.params.running = True
        self.params.disable_current_updates = False
        _LOGGER.debug("Internal charger has been started")


    async def async_update_internal_state_off(self):
        self.params.disable_current_updates = True
        charger_state = self.hub.async_get_chargerobject_value()
        if any([
            charger_state not in self._charger.chargerstates.get(ChargeControllerStates.Charging),
            len(charger_state) < 1
        ]):
            self.params.running = False
            self.params.charger_state_mismatch = False
            _LOGGER.debug("Internal charger has been stopped")
        elif time.time() - self.params.lastest_call_off > 10:
            self.params.charger_state_mismatch = True
            self.params.lastest_call_off = time.time()
            log_once(f"Fail when trying to stop connected charger. Retrying stop-attempt...")



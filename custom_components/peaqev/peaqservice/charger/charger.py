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
    def _chargertype_charger_is_on(self) -> bool:
        if self._hub.chargertype.charger.options.powerswitch_controls_charging:
            return self._hub.sensors.chargerobject_switch.value
        return all(
            [
                self._hub.sensors.chargerobject_switch.value,
                self._hub.sensors.carpowersensor.value > 0
            ]
        )

    @property
    def session_active(self) -> bool:
        return self._params.session_active

    @session_active.setter
    def session_active(self, val):
        self._params.session_active = val

    async def charge(self):
        """Main function to turn charging on or off"""
        if self._params.check_running_state:
            await self._update_charger_state_internal(ChargerStateEnum.Pause)
        if self._hub.sensors.charger_enabled.value is True:
            if not self.session_active:
                self.session.core.reset()
                self.session_active = True
            if self._hub.chargecontroller.status is CHARGERSTATES.Start.name:
                if self._chargertype_charger_is_on is False and self._params.running is False:
                    await self._start_charger()
            elif self._hub.chargecontroller.status in [CHARGERSTATES.Stop.name, CHARGERSTATES.Idle.name]:
                if (self._chargertype_charger_is_on or self._hub.sensors.carpowersensor.value > 0) is True and self._params.stopped is False:
                    await self._pause_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Done.name and self._hub.sensors.charger_done.value is False:
                await self._terminate_charger()
            elif self._hub.chargecontroller.status is CHARGERSTATES.Idle.name:
                self._hub.sensors.charger_done.value = False
                if self._chargertype_charger_is_on is True:
                    await self._terminate_charger()
        else:
            if self._chargertype_charger_is_on is True and self._params.stopped is False:
                if self._hub.sensors.charger_enabled.value is True:
                    _LOGGER.info("Peaqev detected running charger outside of peaqev-session. Stopping charger...")
                    await self._terminate_charger(aux=True)
            return

    async def _start_charger(self):
        if time.time() - self._params.latest_charger_call > CALL_WAIT_TIMER:
            await self._update_charger_state_internal(ChargerStateEnum.Start)
            if self.session_active is False:
                await self._call_charger(ON)
                self.session_active = True
            else:
                await self._call_charger(RESUME)
            self._hub.chargecontroller.update_latestchargerstart()
            if self._hub.chargertype.charger.servicecalls.options.allowupdatecurrent is True and self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data) is False:
                self._hass.async_create_task(self._updatemaxcurrent())

    async def _terminate_charger(self, aux:bool = False):
        if time.time() - self._params.latest_charger_call > CALL_WAIT_TIMER:
            self.session_active = False
            await self._update_charger_state_internal(ChargerStateEnum.Stop)
            self.session_active = False
            await self._call_charger(OFF)
            if not aux:
                self._hub.sensors.charger_done.value = True
            else:
                _LOGGER.info("Peaqev turned off charger because it was running outside of a peaqev-session.")

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
        else:
            await self._hub.state_machine.services.async_call(
                calls[DOMAIN],
                calls[command],
                calls["params"]
            )
        msg = f"Calling charger {command}"
        _LOGGER.debug(msg)
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
                        _LOGGER.debug(f"peaqev updating current with: {calls[DOMAIN]}, {calls[UPDATECURRENT]} and params: {serviceparams}")
                        await self._hub.state_machine.services.async_call(
                            calls[DOMAIN],
                            calls[UPDATECURRENT],
                            serviceparams
                        )
                    await self._hass.async_add_executor_job(self.helpers.wait_loop_cycle)

            if self._hub.chargertype.charger.servicecalls.options.update_current_on_termination is True:
                final_service_params = await self.helpers.setchargerparams(calls, ampoverride=6)
                await self._hub.state_machine.services.async_call(
                    calls[DOMAIN],
                    calls[UPDATECURRENT],
                    final_service_params
                )

    async def _update_charger_state_internal(self, state: ChargerStateEnum):
        if state in [ChargerStateEnum.Start, ChargerStateEnum.Resume]:
            self._params.running = True
            self._params.stopped = False
            self._params.disable_current_updates = False
            _LOGGER.debug("Charger-class has been started")
        elif state in [ChargerStateEnum.Stop, ChargerStateEnum.Pause]:
            self._params.disable_current_updates = True
            charger = self._hub.sensors.chargerobject.value.lower()

            chargingstates = self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]
            if charger not in chargingstates or len(charger) < 1:
                self._params.running = False
                self._params.stopped = True
                self._params.check_running_state = False
                _LOGGER.debug("Charger-class has been stopped")
            else:
                self._params.check_running_state = True
                _LOGGER.debug(f"Tried to stop charger, but chargerobj is: {charger}. Retrying stop-attempt.")

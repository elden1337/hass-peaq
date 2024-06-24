import logging
import time

from peaqevcore.common.enums.calltype_enum import CallTypes
from peaqevcore.common.models.observer_types import ObserverTypes
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.services.chargertype.const import DOMAIN, PARAMS

from custom_components.peaqev.peaqservice.chargecontroller.charger.charger_call_service import \
    call_ok
from custom_components.peaqev.peaqservice.chargecontroller.charger.charger_states import \
    ChargerStates
from custom_components.peaqev.peaqservice.chargecontroller.charger.chargerhelpers import (
    ChargerHelpers, async_set_chargerparams)
from custom_components.peaqev.peaqservice.chargecontroller.charger.chargermodel import \
    ChargerModel
from custom_components.peaqev.peaqservice.hub.const import LookupKeys
from custom_components.peaqev.peaqservice.util.constants import CURRENT
from custom_components.peaqev.peaqservice.util.extensionmethods import \
    log_once_per_minute

_LOGGER = logging.getLogger(__name__)


class Charger:
    def __init__(self, controller):
        self.controller = controller
        self._charger = (
            controller.hub.chargertype
        )  # todo: should not have direct access. route through chargecontroller
        self.model = ChargerModel()
        self.helpers = ChargerHelpers(self)
        self.controller.hub.observer.add(ObserverTypes.PowerCanaryDead, self.async_pause_charger)
        self.controller.hub.observer.add(ObserverTypes.KillswitchDead, self.async_terminate_charger)
        self.controller.hub.observer.add(ObserverTypes.CarConnected, self.async_reset_session)
        self.controller.hub.observer.add(ObserverTypes.ProcessCharger, self.async_charge)

    async def async_setup(self):
        pass

    @property
    def session_active(self) -> bool:
        return self.model.session_active

    @property
    def charger_active(self) -> bool:
        if self._charger.options.powerswitch_controls_charging:
            return (
                self.controller.hub.sensors.chargerobject_switch.value
            )  # todo: composition
        return all(
            [
                self.controller.hub.sensors.carpowersensor.value
                > 0,  # todo: composition
            ]
        )

    async def async_charge(self) -> None:
        """Main function to turn charging on or off"""
        if self.model.unsuccessful_stop:
            await self.async_internal_state(ChargerStates.Pause)
        if (
            self.controller.hub.enabled
            and not self.controller.hub.sensors.power.killswitch.is_dead
        ):
            await self.async_reset_session()
            match self.controller.status_type:
                case ChargeControllerStates.Start:
                    await self.async_start_case()
                case ChargeControllerStates.Stop | ChargeControllerStates.Error:
                    await self.async_stop_case()
                case ChargeControllerStates.Done | ChargeControllerStates.Idle:
                    await self.async_done_idle_case()
                case ChargeControllerStates.Connected | ChargeControllerStates.Disabled:
                    pass
                case _:
                    _LOGGER.error(
                        f'Could not match any chargecontroller-state. state: {self.controller.status_type}'
                    )
        else:
            if self.charger_active and self.model.running:
                if self.controller.hub.sensors.power.killswitch.is_dead:
                    _LOGGER.debug(
                        f'Powersensor has failed to update for more than {self.controller.hub.sensors.power.killswitch.total_timer}s. Charging is paused until it comes alive again.'
                    )
                elif self.controller.hub.enabled:
                    _LOGGER.debug(
                        'Detected charger running outside of peaqev-session, overtaking command and pausing.'
                    )
                await self.async_pause_charger()

    async def async_done_idle_case(self) -> None:
        _state = self.controller.status_type
        if (
            not self.controller.hub.charger_done
            and _state is ChargeControllerStates.Done
        ):
            await self.async_terminate_charger()
        elif self.charger_active and _state is ChargeControllerStates.Idle:
            _LOGGER.debug('Going to terminate since the car has been disconnected.')
            await self.async_terminate_charger()

    async def async_stop_case(self) -> None:
        if self.charger_active:
            if not self.model.running and not self.session_active:
                _LOGGER.debug(
                    'Detected charger running outside of peaqev-session, overtaking command and pausing.'
                )
            await self.async_pause_charger()

    async def async_start_case(self) -> None:
        if not self.model.running:
            if not self.charger_active:
                await self.async_start_charger()
            else:
                _LOGGER.debug(
                    'Detected charger running outside of peaqev-session, overtaking command.'
                )
                await self.async_overtake_charger()
        # elif (
        #     not self.charger_active
        # ):  # interim solution to test if case works with Garo and other types.
        #     _LOGGER.debug(
        #         "Restarting charger since it has been turned off from outside of Peaqev."
        #     )
        #     await self.async_start_charger()

    async def async_reset_session(self) -> None:
        if (
            not self.session_active
            and self.controller.status_type is not ChargeControllerStates.Done
        ):
            await self.controller.session.async_reset(
                getattr(
                    self.controller.hub.sensors.locale.data.query_model,
                    'charged_peak',
                    0,
                )
            )
            self.model.session_active = True

    async def async_overtake_charger(self) -> None:
        await self.async_internal_state(ChargerStates.Start)
        self.model.session_active = True
        await self.async_post_start_charger()

    async def async_start_charger(self) -> None:
        if call_ok(self.model.latest_charger_call):
            await self.async_internal_state(ChargerStates.Start)
            if not self.session_active:
                await self.async_call_charger(CallTypes.On)
                self.model.session_active = True
            else:
                await self.async_call_charger(CallTypes.Resume)
            await self.async_post_start_charger()

    async def async_post_start_charger(self) -> None:
        await self.controller.async_update_latest_charger_start()
        if (
            self._charger.servicecalls.options.allowupdatecurrent
            and not await self.controller.hub.async_free_charge()
        ):
            self.controller.hub.state_machine.async_create_task(
                self.async_update_max_current()
            )

    async def async_terminate_charger(self) -> None:
        if call_ok(self.model.latest_charger_call):
            await self.controller.session.async_terminate()
            await self.async_internal_state(ChargerStates.Stop)
            self.model.session_active = False
            await self.async_call_charger(CallTypes.Off)
            await self.controller.hub.observer.async_broadcast(
                ObserverTypes.UpdateChargerDone, True
            )

    async def async_pause_charger(self) -> None:
        if call_ok(self.model.latest_charger_call):
            if (
                self.controller.hub.charger_done
                or self.controller.status_type is ChargeControllerStates.Idle
            ):
                await self.async_terminate_charger()
            else:
                await self.async_internal_state(ChargerStates.Pause)
                await self.async_call_charger(CallTypes.Pause)

    async def async_call_charger(self, command: CallTypes) -> None:
        try:
            calls = self._charger.servicecalls.get_call(command)
            await self.async_do_update(
                calls.get(DOMAIN), calls.get(command), calls.get(PARAMS)
            )
            self.model.latest_charger_call = time.time()
        except Exception as e:
            _LOGGER.error(f'Error calling charger: {e}')

    async def async_update_max_current(self) -> None:
        calls = self._charger.servicecalls.get_call(CallTypes.UpdateCurrent)
        if await self.controller.hub.state_machine.async_add_executor_job(
            self.helpers.wait_turn_on
        ):
            # call here to set amp-list
            while all(
                [
                    self.controller.hub.sensors.chargerobject_switch.value,
                    self.model.running,
                ]
            ):
                if await self.controller.hub.state_machine.async_add_executor_job(
                    self.helpers.wait_update_current
                ):
                    serviceparams = await async_set_chargerparams(
                        calls,
                        await self.controller.hub.threshold.async_allowed_current(),
                    )
                    if (
                        not self.model.disable_current_updates
                        and await self.controller.hub.power.power_canary.async_allow_adjustment(
                            new_amps=serviceparams[calls[PARAMS][CURRENT]]
                        )
                    ):
                        await self.async_do_service_call(
                            calls[DOMAIN], calls[CallTypes.UpdateCurrent], serviceparams
                        )
                    await self.controller.hub.state_machine.async_add_executor_job(
                        self.helpers.wait_loop_cycle
                    )

            if self._charger.servicecalls.options.update_current_on_termination is True:
                final_service_params = await async_set_chargerparams(calls, 6)
                await self.async_do_service_call(
                    calls[DOMAIN], calls[CallTypes.UpdateCurrent], final_service_params
                )

    async def async_internal_state(self, state: ChargerStates) -> None:
        if state in [ChargerStates.Start, ChargerStates.Resume]:
            self._internal_state_on()
        elif state in [ChargerStates.Stop, ChargerStates.Pause]:
            await self.async_internal_state_off()

    def _internal_state_on(self):
        self.model.running = True
        self.model.disable_current_updates = False
        _LOGGER.debug('Internal charger has been started')

    async def async_internal_state_off(self):
        self.model.disable_current_updates = True
        charger_state = await self.controller.hub.async_request_sensor_data(LookupKeys.CHARGEROBJECT_VALUE)
        if charger_state not in self._charger.chargerstates.get(
            ChargeControllerStates.Charging
        ):
            self.model.running = False
            self.model.unsuccessful_stop = False
            _LOGGER.debug('Internal charger has been stopped')
        elif time.time() - self.model.lastest_call_off > 10:
            self.model.unsuccessful_stop = True
            self.model.lastest_call_off = time.time()
            log_once_per_minute(
                f'Fail when trying to stop connected charger. Retrying stop-attempt...', 'warning'
            )

    async def async_do_update(self, calls_domain, calls_command, calls_params) -> bool:
        if self._charger.servicecalls.options.switch_controls_charger:
            return await self.async_do_outlet_update(calls_command)
        else:
            return await self.async_do_service_call(
                calls_domain, calls_command, calls_params
            )

    async def async_do_outlet_update(self, call) -> bool:
        _LOGGER.debug('Calling charger-outlet')
        try:
            self.controller.hub.state_machine.states.async_set(
                self._charger.entities.powerswitch, call
            )  # todo: composition
        except Exception as e:
            _LOGGER.error(f'Error in async_do_outlet_update: {e}')
            return False
        return True

    async def async_do_service_call(self, domain, command, params) -> bool:
        _domain = domain
        if params.get('domain', None) is not None:
            _domain = params.pop('domain')

        _LOGGER.debug(
            f"Calling charger {command} for domain '{domain}' with parameters: {params}"
        )
        try:
            await self.controller.hub.state_machine.services.async_call(
                _domain, command, params
            )
        except Exception as e:
            _LOGGER.error(f'Error in async_do_service_call: {e}')
            return False
        return True

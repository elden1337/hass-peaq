import logging

_LOGGER = logging.getLogger(__name__)


async def async_do_update(state_machine, calls_domain, calls_command, calls_params, switch_controls_charger) -> bool:
    if switch_controls_charger:
        return await _async_do_outlet_update(calls_command, state_machine)
    else:
        return await async_do_service_call(calls_domain, calls_command, calls_params, state_machine)


async def _async_do_outlet_update(self, call, state_machine) -> bool:
    _LOGGER.debug("Calling charger-outlet")
    try:
        await state_machine.states.async_set(self._charger.entities.powerswitch, call)  # todo: composition
    except Exception as e:
        _LOGGER.error(f"Error in async_do_outlet_update: {e}")
        return False
    return True


async def async_do_service_call(self, domain, command, params, state_machine) -> bool:
    _LOGGER.debug(f"Calling charger {command} for domain '{domain}' with parameters: {params}")
    try:
        await self.hub.state_machine.services.async_call(
            domain,
            command,
            params
        )
    except Exception as e:
        _LOGGER.error(f"Error in async_do_service_call: {e}")
        return False
    return True

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import \
    ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import \
    ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade


class ChargeControllerFactory:
    @staticmethod
    async def async_create(hub, charger_states, charger_type, observer: IObserver, state_machine: IHomeAssistantFacade) -> IChargeController:
        if hub.options.peaqev_lite:
            controller = ChargeControllerLite(hub, charger_states, charger_type, observer, state_machine)
        else:
            controller = ChargeController(hub, charger_states, charger_type, observer, state_machine)

        await controller.async_setup()
        return controller

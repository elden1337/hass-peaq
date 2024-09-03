from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import \
    ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import \
    ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController


class ChargeControllerFactory:
    @staticmethod
    async def async_create(hub, observer, charger_states, charger_type) -> IChargeController:
        if hub.options.peaqev_lite:
            controller = ChargeControllerLite(hub, observer, charger_states, charger_type)
        else:
            controller = ChargeController(hub, observer, charger_states, charger_type)

        await controller.async_setup()
        return controller

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import \
    ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import \
    ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import \
    IChargeController
from custom_components.peaqev.peaqservice.chargertypes.chargertype_factory import ChargerTypeFactory


class ChargeControllerFactory:
    @staticmethod
    async def async_create(hub) -> IChargeController:
        charger_type = await ChargerTypeFactory.async_create(hub.state_machine, hub.options)
        if hub.options.peaqev_lite:
            controller = ChargeControllerLite(hub, charger_type)
        else:
            controller = ChargeController(hub, charger_type)

        await controller.async_setup()
        return controller


from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController


class ChargeControllerFactory:
    @staticmethod
    async def async_create(hub, charger_states, charger_type) -> IChargeController:
        if hub.options.peaqev_lite:
            return ChargeControllerLite(hub, charger_states, charger_type)
        else:
            return ChargeController(hub, charger_states, charger_type)
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite
from custom_components.peaqev.peaqservice.chargecontroller.ichargecontroller import IChargeController


class ChargeControllerFactory:
    @staticmethod
    def create(hub, charger_states) -> IChargeController:
        if hub.options.peaqev_lite:
            return ChargeControllerLite(hub, charger_states)
        return ChargeController(hub, charger_states)
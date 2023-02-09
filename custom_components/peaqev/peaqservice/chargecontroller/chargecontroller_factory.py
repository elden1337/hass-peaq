from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_lite import ChargeControllerLite


class ChargeControllerFactory:
    @staticmethod
    def create(hub):
        if hub.options.peaqev_lite:
            return ChargeControllerLite(hub)
        return ChargeController(hub)
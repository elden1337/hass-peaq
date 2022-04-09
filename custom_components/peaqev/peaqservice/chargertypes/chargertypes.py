import custom_components.peaqev.peaqservice.constants as constants
from homeassistant.core import HomeAssistant
import logging

from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee

_LOGGER = logging.getLogger(__name__)

class ChargerTypeData():
    """Init the service"""
    def __init__(self, hass: HomeAssistant, input, chargerid):
        self._charger = None
        self._type = input
        self._hass = hass
        self._chargerid = chargerid

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self._charger = ChargeAmps(self._hass, self._chargerid)
        elif  input == constants.CHARGERTYPE_EASEE:
            self._charger = Easee(self._hass, self._chargerid)

        self.validatecharger()

    @property
    def type(self) -> str:
        return self._type

    @property
    def charger(self):
        return self._charger

    def validatecharger(self):
        try:
            assert len(self._charger.chargerentity) > 0
            assert len(self._charger.powermeter) > 0
            assert len(self._charger.powerswitch) > 0
            assert self._charger.servicecalls["domain"] is not None
            assert self._charger.servicecalls["on"] is not None
            assert self._charger.servicecalls["off"] is not None
            if self._charger.allowupdatecurrent:
                assert self._charger.servicecalls["updatecurrent"] is not None
        except Exception as e:
            _LOGGER.error("Peaq could not initialize charger", e)






import custom_components.peaqev.peaqservice.constants as constants
import homeassistant.helpers.template as template
from homeassistant.core import HomeAssistant
import logging

from custom_components.peaqev.peaqservice.chargertype.chargeamps import ChargeAmps
from custom_components.peaqev.peaqservice.chargertype.easee import Easee

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


class ChargerBase():
    def __init__(self, hass, currentupdate:bool):
        self._hass = hass
        self._chargerEntity = None
        self._powermeter = None
        self._powerswitch = None
        self._allowupdatecurrent = currentupdate
        self.ampmeter = None
        self.ampmeter_is_attribute = None
        self._servicecalls = {}
        self._chargerstates = {
            "idle": [],
            "connected": [],
            "charging": []
        }
        
    @property
    def chargerstates(self) -> dict:
        return self._chargerstates

    @property
    def allowupdatecurrent(self) -> bool:
        return self._allowupdatecurrent

    """Power meter"""
    @property
    def powermeter(self):
        return self._powermeter

    @powermeter.setter
    def powermeter(self, val):
        assert type(val) is str
        self._powermeter = val

    """Power Switch"""
    @property
    def powerswitch(self):
        return self._powerswitch

    @powerswitch.setter
    def powerswitch(self, val):
        assert type(val) is str
        self._powerswitch = val

    """Charger entity"""
    @property
    def chargerentity(self):
        return self._chargerentity

    @chargerentity.setter
    def chargerentity(self, val):
        assert type(val) is str
        self._chargerentity = val

    """Service calls"""
    @property
    def servicecalls(self) -> dict:
        return self._servicecalls

    @servicecalls.setter
    def servicecalls(self, obj):
        assert type(obj) is dict
        self._servicecalls = obj




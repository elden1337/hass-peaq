
class ChargerBase():
    def __init__(self, hass, currentupdate: bool):
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

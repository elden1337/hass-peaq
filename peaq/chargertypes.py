import custom_components.peaq.constants as constants

"""Init the service"""
class ChargerTypeData():
    def __init__(self, input):
        self._Charger = None
        self._Type = input

        if input == constants.CHARGERTYPE_CHARGEAMPS:
            self.Charger = ChargeAmps()
        elif  input == constants.CHARGERTYPE_EASEE:
            self.Charger = Easee()
    
    @property
    def Type(self) -> str:
        return self._Type

    @property
    def Charger(self):
        return self._Charger

    @Charger.setter
    def Charger(self, obj):
        self._Charger = obj

"""Shared baseclass"""
class ChargerTypeBase():
    def __init__(self):
        self._PowerMeter = ""
        self._PowerSwitch = ""
        self._ChargerEntity = ""
        self._ServiceCalls = {}     

    """Power meter"""
    @property
    def PowerMeter(self):
        return self._PowerMeter

    @PowerMeter.setter
    def PowerMeter(self, obj):
        self._PowerMeter = obj

    """Power Switch"""
    @property
    def PowerSwitch(self):
        return self._PowerSwitch

    @PowerSwitch.setter
    def PowerSwitch(self, obj):
        self._PowerSwitch = obj

    """Charger entity"""
    @property
    def ChargerEntity(self):
        return self._ChargerEntity

    @ChargerEntity.setter
    def ChargerEntity(self, obj):
        self._ChargerEntity = obj

    """Service calls"""
    @property
    def ServiceCalls(self) -> dict:
        return self._ServiceCalls

    @ServiceCalls.setter
    def ServiceCalls(self, obj):
        assert type(obj) is dict
        self._ServiceCalls = obj

class ChargeAmps(ChargerTypeBase):
    def __init__(self):
        super().__init__()
        self.ChargerEntity = "sensor.hake_2012019145m_1"
        self.PowerMeter = "sensor.hake_2012019145m_1_power"
        self.PowerSwitch = "switch.hake_2012019145m_1" 
        self.ServiceCalls = {

        }

class Easee(ChargerTypeBase):
    def __init__(self):
        super().__init__()

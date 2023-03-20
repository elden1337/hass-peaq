# from dataclasses import dataclass, field
# from peaqevcore.models.chargecontroller_states import ChargeControllerStates

# @dataclass
# class ChargeAmps(ChargerType):
#     _chargeramps_type = ""
#     _chargeamps_connector = 1  # fix this later to be able to use aura




# @dataclass
# class ChargerType:
#     _hass = None
#     _type = chargertype
#     chargerstates:dict = field(default_factory={})
#     _chargerid = huboptions.charger.chargerid
#     entities.imported_entityendings = entity_endings
#     options.powerswitch_controls_charging = True
    
#     def __post_init__(self, hass):
#         self._hass = hass
#         self.chargerstates[ChargeControllerStates.Idle] = ["available"]
#         self.chargerstates[ChargeControllerStates.Connected] = ["connected"]
#         self.chargerstates[ChargeControllerStates.Charging] = ["charging"]


#     def __set_default_chargerstates(self) -> dict:
#         return {
#             ChargeControllerStates.Idle: [],
#             ChargeControllerStates.Connected: [],
#             ChargeControllerStates.Charging: [],
#             ChargeControllerStates.Done: []
#         }



from dataclasses import dataclass, field
from enum import Enum

class SensorTypes(Enum):
    ChargerEntity = 1
    PowerMeter = 2
    AmpMeter = 3
    PowerSwitch = 4
    MaxAmps = 5

"""chargeamps"""
# self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
# self.entities.powermeter = f"sensor.{self.entities.entityschema}_1_power"
# self.entities.ampmeter = "max_current"
# self.entities.powerswitch = self._determine_switch_entity()
# self.options.ampmeter_is_attribute = True
# self._chargeramps_type = self._set_chargeamps_type(self.entities.chargerentity)

"""easee"""
# amp_sensor = f"sensor.{self.entities.entityschema}_dynamic_charger_limit"
# if not self._validate_sensor(amp_sensor):
#     amp_sensor = f"sensor.{self.entities.entityschema}_max_charger_limit"
# self.entities.maxamps = f"sensor.{self.entities.entityschema}_max_charger_limit"
# self.entities.chargerentity = f"sensor.{self.entities.entityschema}_status"
# self.entities.powermeter = f"sensor.{self.entities.entityschema}_power"
# self.options.powermeter_factor = 1000
# self.entities.powerswitch = f"switch.{self.entities.entityschema}_is_enabled"
# self.entities.ampmeter = amp_sensor
# self.options.ampmeter_is_attribute = False



SENSORS_SCHEMA = {
    SensorTypes.ChargerEntity: "sensor.{}_1",
    SensorTypes.PowerMeter: "sensor.{}_1_power",
    SensorTypes.AmpMeter: "max_current"
    #SensorTypes.PowerSwitch:""
}

#only set the ones that are interesting here. all others should go by default.
OPTIONS_SCHEMA = {
#self.options.ampmeter_is_attribute = True
#self.options.powerswitch_controls_charging = True
# allowupdatecurrent=True,
# update_current_on_termination=True,
# switch_controls_charger=False
#self.options.powermeter_factor = 1000
}

#below here is generic stuff

REQUIRED_SENSORTYPES = [SensorTypes.ChargerEntity]

@dataclass
class Test:
    chargerid: str #remove this when huboptions are there
    _sensors: {} = field(init=False)
    #huboptions: HubOptions
    #chargertype: Any
    #hass: HomeAssistant

    def __post_init__(self):
        self.__setup_sensors()

    def __setup_sensors(self):
        for type in SensorTypes:
            self._sensors[type] = SENSORS_SCHEMA.get(type) \
                .format(self.chargerid)
                #.format(self.huboptions.charger.chargerid)
        self.__check_required_sensors()

    def __check_required_sensors(self) -> bool:
        for r in REQUIRED_SENSORTYPES:
            assert r in self._sensors.keys()
        return True


t = Test("abcsds")
print(t._sensors)
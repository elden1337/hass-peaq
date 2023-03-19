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

SCHEMA = {
    "powersensor": "sensor.{}_powersensor"
}

@dataclass
class Test:
    _sensor: str = field(init=False)
    _chargerid: str

    def __post_init__(self):
        self._sensor = SCHEMA.get("powersensor").format(self._chargerid)


t = Test("abcsds")
print(t._sensor)
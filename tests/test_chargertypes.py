from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData
from peaqevcore.hub.hub_options import HubOptions


def test_chargeamps_halo(hass):
    options = HubOptions()
    options.charger.chargertype = "Chargeamps"
    options.charger.chargerid = "1234567890A"
    c = ChargerTypeData(
            hass=hass,
            input_type=options.charger.chargertype,
            options=options
        )
    print(c)
    assert c.type.value == "chargeamps"

def test_easee():
    pass

def test_zaptec_go():
    pass
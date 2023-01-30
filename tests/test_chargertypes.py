from peaqevcore.hub.hub_options import HubOptions

from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData


def test_chargeamps_halo(hass):
    options = HubOptions()
    options.charger.chargertype = "Chargeamps"
    options.charger.chargerid = "1234567890A"
    c = ChargerTypeData(
            hass=hass,
            input_type=options.charger.chargertype,
            options=options
        )
    assert c.type.value == "chargeamps"

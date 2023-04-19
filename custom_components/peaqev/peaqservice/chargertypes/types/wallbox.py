import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.constants import CURRENT
from custom_components.peaqev.peaqservice.util.extensionmethods import log_once

_LOGGER = logging.getLogger(__name__)
# docs: https://github.com/kirei/hass-chargeamps

# CHARGEPOINT = "chargepoint"
# CONNECTOR = "connector"


class Wallbox(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        _LOGGER.warning(
            "You are initiating Wallbox as Chargertype. Bare in mind that this chargertype has not been signed off in testing and may be very unstable."
        )
        self._hass = hass
        self._is_initialized = False
        self._type = chargertype
        
        self._chargerid = huboptions.charger.chargerid #needed?
        
        self.entities.imported_entityendings = self.entity_endings
        self.options.powerswitch_controls_charging = True
        self.chargerstates[ChargeControllerStates.Idle] = ["available"]
        self.chargerstates[ChargeControllerStates.Connected] = ["connected"]
        self.chargerstates[ChargeControllerStates.Charging] = ["charging"]

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "wallbox"

    # @property
    # def max_amps(self) -> int:
    #     return self.get_allowed_amps()

    # @property
    # def entity_endings(self) -> list:
    #     """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
    #     return [
    #         "_power",
    #         "_1",
    #         "_2",
    #         "_status",
    #         "_dimmer",
    #         "_downlight",
    #         "_current",
    #         "_voltage",
    #     ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
            "Charging",
            "Discharging",
            "Paused",
            "Scheduled",
            "Waiting for car demand",
            "Waiting",
            "Disconnected",
            "Error",
            "Ready",
            "Locked",
            "Locked, car connected",
            "Updating",
            "Waiting in queue by Power Sharing",
            "Waiting in queue by Power Boost",
            "Waiting MID failed",
            "Waiting MID safety margin exceeded",
            "Waiting in queue by Eco-Smart",
            "Unknown"
            ]

    @property
    def call_on(self) -> CallType:
        return CallType(CallTypes.On.value, {})

    @property
    def call_off(self) -> CallType:
        return CallType(CallTypes.Off.value, {})

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            call="set_value",
            params={"entity_id": self.entities.ampmeter, CURRENT: "value"},
            domain="number"
            )

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=False,
            switch_controls_charger=True,
        )

    # def get_allowed_amps(self) -> int:
    #     """no such method for chargeamps available right now."""
    #     return 16

    # def _determine_entities(self) -> list:
    #     ret = []
    #     for e in self.entities.imported_entities:
    #         entity_state = self._hass.states.get(e)
    #         if entity_state != "unavailable":
    #             ret.append(e)
    #     return ret

    # def _set_chargeamps_type(self, main_sensor_entity) -> ChargeAmpsTypes:
    #     if self._hass.states.get(main_sensor_entity) is not None:
    #         chargeampstype = self._hass.states.get(main_sensor_entity).attributes.get("chargepoint_type")
    #         return ChargeAmpsTypes.get_type(chargeampstype)

    # def _determine_switch_entity(self) -> str:
    #     ent = self._determine_entities()
    #     for e in ent:
    #         if e.startswith("switch."):
    #             amps = self._hass.states.get(e).attributes.get("max_current")
    #             if isinstance(amps, int):
    #                 return e
    #     raise Exception

    async def async_set_sensors(self) -> None:
        self.entities.maxamps = f"sensor.{self.entities.entityschema}_max_charging_current"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_charging_power"
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f"switch.{self.entities.entityschema}_paused"
        self.entities.ampmeter = f"number.{self.entities.entityschema}_max_charging_current"
        #self.entities.chargerentity = f"sensor.{self.entities.entityschema}_1"
        

    def get_allowed_amps(self) -> int:
        ret = self._hass.states.get(self.entities.maxamps)
        if ret is not None:
            log_once(f"Got max amps from Wallbox. Setting {ret.state}A.")
            return int(ret.state)
        else:
            log_once(
                f"Unable to get max amps. The sensor {self.entities.maxamps} returned state {ret}. Setting max amps to 16 til I get a proper state."
            )
        return 16
    
    # async def async_determine_entities(self) -> list:
    #     ret = []
    #     for e in self.entities.imported_entities:
    #         entity_state = self._hass.states.get(e)
    #         if entity_state != "unavailable":
    #             ret.append(e)
    #     return ret


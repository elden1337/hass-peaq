import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.util.constants import CURRENT

_LOGGER = logging.getLogger(__name__)

# docs: https://github.com/home-assistant/core/tree/dev/homeassistant/components/keba


class Keba(IChargerType):
    def __init__(self, hass: HomeAssistant, huboptions: HubOptions, chargertype):
        _LOGGER.warning(
            "You are initiating Keba as Chargertype. Bare in mind that this chargertype has not been signed off in testing and may be very unstable. Report findings to the developer."
        )
        self._hass = hass
        self._is_initialized = False
        self._type = chargertype

        #self._chargerid = huboptions.charger.chargerid  # needed?

        self.entities.imported_entityendings = self.entity_endings
        self.options.powerswitch_controls_charging = False
        self.chargerstates[ChargeControllerStates.Idle] = ["not ready for charging"]
        self.chargerstates[ChargeControllerStates.Connected] = ["ready for charging"]
        self.chargerstates[ChargeControllerStates.Charging] = ["starting", "charging"]

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "keba"

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return [
            "_max_current",
            "_energy_target",
            "_charging_power",
            "_session_energy",
            "_total_energy",
        ]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return [
        "starting",
        "not ready for charging",
        "ready for charging",
        "charging",
        "error",
        "authorization rejected"
        ]

    @property
    def call_on(self) -> CallType:
        return CallType(
            "enable",
            {},
        )

    @property
    def call_off(self) -> CallType:
        return CallType(
            "disable",
            {},
        )

    @property
    def call_resume(self) -> CallType:
        return self.call_on

    @property
    def call_pause(self) -> CallType:
        return self.call_off

    @property
    def call_update_current(self) -> CallType:
        return CallType(
            "set_current",
            {CURRENT: "current"},
        )

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=True,
            update_current_on_termination=True,
            switch_controls_charger=False,
        )

    async def async_set_sensors(self) -> None:
        self.entities.maxamps = f"sensor.{self.entities.entityschema}_Max_Current"
        self.entities.powermeter = f"sensor.{self.entities.entityschema}_Charging_Power"
        self.options.powermeter_factor = 1000
        self.entities.powerswitch = f"binary_sensor.{self.entities.entityschema}_Status"
        self.entities.ampmeter = f"sensor.{self.entities.entityschema}_Max_Current"
        self.entities.chargerentity = f"binary_sensor.{self.entities.entityschema}_Charging_State|status"


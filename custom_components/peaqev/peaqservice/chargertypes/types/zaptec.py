import logging

from homeassistant.core import HomeAssistant
from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.servicecalls_dto import ServiceCallsDTO
from peaqevcore.models.chargertype.servicecalls_options import \
    ServiceCallsOptions

import custom_components.peaqev.peaqservice.chargertypes.entitieshelper as helper
from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions

_LOGGER = logging.getLogger(__name__)

# docs: https://github.com/custom-components/zaptec


class Zaptec(IChargerType):
    def __init__(
        self,
        hass: HomeAssistant,
        huboptions: HubOptions,
        chargertype,
        auth_required: bool = False,
    ):
        self._hass = hass
        self._type = chargertype
        self._chargerid = huboptions.charger.chargerid
        self.entities.imported_entityendings = self.entity_endings
        self._auth_required = auth_required
        self.options.powerswitch_controls_charging = True

        self.chargerstates[ChargeControllerStates.Idle] = ["disconnected"]
        self.chargerstates[ChargeControllerStates.Connected] = ["waiting"]
        self.chargerstates[ChargeControllerStates.Charging] = ["charging"]
        self.chargerstates[ChargeControllerStates.Done] = ["charge_done"]

    async def async_setup(self) -> bool:
        try:
            entitiesobj = await helper.async_set_entitiesmodel(
                hass=self._hass,
                domain=self.domain_name,
                entity_endings=self.entity_endings,
                entity_schema=self.entities.entityschema,
            )
            self.entities.imported_entities = entitiesobj.imported_entities
            self.entities.entityschema = entitiesobj.entityschema
        except:
            _LOGGER.debug(f"Could not get a proper entityschema for {self.domain_name}.")
            return False

        try:
            await self.async_set_sensors()
        except Exception:
            return False

        await self.async_set_servicecalls(
            domain=self.domain_name,
            model=ServiceCallsDTO(
                on=self.call_on,
                off=self.call_off,
                resume=self.call_resume,
                pause=self.call_pause,
            ),
            options=self.servicecalls_options,
        )
        return True

    @property
    def type(self) -> ChargerType:
        """type returns the implemented chargertype."""
        return self._type

    @property
    def domain_name(self) -> str:
        """declare the domain name as stated in HA"""
        return "zaptec"

    @property
    def entity_endings(self) -> list:
        """declare a list of strings with sensor-endings to help peaqev find the correct sensor-schema."""
        return ["_switch", ""]

    @property
    def native_chargerstates(self) -> list:
        """declare a list of the native-charger states available for the type."""
        return ["unknown", "charging", "disconnected", "waiting", "charge_done"]

    @property
    def max_amps(self) -> int:
        return 16

    @property
    def call_on(self) -> CallType:
        return CallType("start_charging", {"charger_id": self._chargerid})

    @property
    def call_off(self) -> CallType:
        return CallType("stop_charging", {"charger_id": self._chargerid})

    @property
    def call_resume(self) -> CallType:
        return CallType("resume_charging", {"charger_id": self._chargerid})

    @property
    def call_pause(self) -> CallType:
        return CallType("stop_pause_charging", {"charger_id": self._chargerid})

    @property
    def call_update_current(self) -> CallType:
        raise NotImplementedError

    @property
    def servicecalls_options(self) -> ServiceCallsOptions:
        return ServiceCallsOptions(
            allowupdatecurrent=False,
            update_current_on_termination=False,
            switch_controls_charger=False,
        )

    async def async_set_sensors(self):
        try:
            self.entities.chargerentity = f"sensor.zaptec_{self.entities.entityschema}"
            self.entities.powermeter = f"{self.entities.chargerentity}|total_charge_power"
            self.options.powermeter_factor = 1
            self.entities.powerswitch = f"switch.zaptec_{self.entities.entityschema}_switch"
            _LOGGER.debug("Sensors for Zaptec have been set up.")
        except Exception as e:
            _LOGGER.exception(f"Could not set needed sensors for Zaptec. {e}")

    def _validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True

    async def async_validate_sensor(self, sensor: str) -> bool:
        ret = self._hass.states.get(sensor)
        if ret is None:
            return False
        elif ret.state == "Null":
            return False
        return True

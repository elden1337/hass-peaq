
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.hub.hubdata.hubdatabase import HubDataBase
from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import HubMember
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME, HOURLY
)


class HubDataLite(HubDataBase):
    totalhourlyenergy: HubMember

    def create_hub_data(
            self,
            hass,
            config_inputs:dict,
            domain: str
    ):
        self.create_hub_base_data(hass, config_inputs, domain)

        self.totalhourlyenergy = HubMember(
            data_type=float,
            listenerentity=f"sensor.{domain}_{ex.nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
            initval=0
        )

    def init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        self.chargerobject.value = self.hass.states.get(self.chargerobject.entity).state if self.hass.states.get(
            self.chargerobject.entity) is not None else 0
        self.chargerobject_switch.value = self.hass.states.get(
            self.chargerobject_switch.entity).state if self.hass.states.get(
            self.chargerobject_switch.entity) is not None else ""
        self.chargerobject_switch.updatecurrent()
        self.carpowersensor.value = self.hass.states.get(self.carpowersensor.entity).state if self.hass.states.get(
            self.carpowersensor.entity) is not None else 0
        self.totalhourlyenergy.value = self.hass.states.get(self.totalhourlyenergy.entity) if self.hass.states.get(
            self.totalhourlyenergy.entity) is not None else 0

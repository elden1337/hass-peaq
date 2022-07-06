

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.hub.hubdata.hubdatabase import HubDataBase
from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import HubMember
from custom_components.peaqev.peaqservice.power.power import Power
from custom_components.peaqev.peaqservice.util.constants import (
    AVERAGECONSUMPTION,
    AVERAGECONSUMPTION_24H,
    CONSUMPTION_TOTAL_NAME,
    HOURLY
)

class HubData(HubDataBase):
    powersensor_includes_car: bool
    powersensormovingaverage: HubMember
    totalhourlyenergy: HubMember
    power: Power

    def create_hub_data(
            self,
            hass,
            config_inputs:dict,
            domain: str):

        self.powersensor_includes_car = bool(config_inputs["powersensorincludescar"])
        self.create_hub_base_data(hass, config_inputs, domain)

        self.powersensormovingaverage = HubMember(
            data_type=int,
            listenerentity=f"sensor.{domain}_{ex.nametoid(AVERAGECONSUMPTION)}",
            initval=0
        )
        self.powersensormovingaverage24 = HubMember(
            data_type=int,
            listenerentity=f"sensor.{domain}_{ex.nametoid(AVERAGECONSUMPTION_24H)}",
            initval=0
        )
        self.totalhourlyenergy = HubMember(
            data_type=float,
            listenerentity=f"sensor.{domain}_{ex.nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
            initval=0
        )
        self.power = Power(
            configsensor=config_inputs["powersensor"],
            powersensor_includes_car=self.powersensor_includes_car
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

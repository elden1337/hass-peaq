from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData
from custom_components.peaqev.peaqservice.hub.hubmember import CurrentPeak, HubMember, CarPowerSensor, ChargerSwitch
from custom_components.peaqev.peaqservice.hub.power import Power
from custom_components.peaqev.peaqservice.localetypes.locale import LocaleData
import custom_components.peaqev.peaqservice.util.constants as constants
import custom_components.peaqev.peaqservice.util.extensionmethods as ex

class HubData:
    _powersensor_includes_car: bool
    locale: LocaleData
    chargertype: ChargerTypeData
    currentpeak: CurrentPeak
    charger_enabled: HubMember
    powersensormovingaverage: HubMember
    totalhourlyenergy: HubMember
    charger_done: HubMember
    power: Power
    carpowersensor: CarPowerSensor
    chargerobject: HubMember
    carpowersensor: CarPowerSensor
    chargerobject_switch: ChargerSwitch

    def create_hub_data(
            self,
            hass,
            config_inputs:dict,
            domain: str):

        self._powersensor_includes_car = bool(config_inputs["powersensorincludescar"])

        self.locale = LocaleData(
            config_inputs["locale"],
            domain
        )
        self.chargertype = ChargerTypeData(
            hass,
            config_inputs["chargertype"],
            config_inputs["chargerid"]
        )
        self.currentpeak = CurrentPeak(
            type=float,
            listenerentity=self.locale.current_peak_entity,
            initval=0,
            startpeaks=config_inputs["startpeaks"]
        )
        self.charger_enabled = HubMember(
            type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(constants.CHARGERENABLED)}",
            initval=False
        )
        self.powersensormovingaverage = HubMember(
            type=int,
            listenerentity=f"sensor.{domain}_{ex.nametoid(constants.AVERAGECONSUMPTION)}",
            initval=0
        )
        self.totalhourlyenergy = HubMember(
            type=float,
            listenerentity=f"sensor.{domain}_{ex.nametoid(constants.CONSUMPTION_TOTAL_NAME)}_{constants.HOURLY}",
            initval=0
        )
        self.charger_done = HubMember(
            type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(constants.CHARGERDONE)}",
            initval=False
        )
        self.power = Power(
            configsensor=config_inputs["powersensor"],
            powersensor_includes_car=self._powersensor_includes_car
        )
        self.carpowersensor = CarPowerSensor(
            type=int,
            listenerentity=self.chargertype.charger.powermeter,
            initval=0,
            powermeter_factor=self.chargertype.charger.powermeter_factor
        )
        self.chargerobject = HubMember(
            type=str,
            listenerentity=self.chargertype.charger.chargerentity
        )
        self.chargerobject_switch = ChargerSwitch(
            hass=hass,
            type=bool,
            listenerentity=self.chargertype.charger.powerswitch,
            initval=False,
            currentname=self.chargertype.charger.ampmeter,
            ampmeter_is_attribute=self.chargertype.charger.ampmeter_is_attribute
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
        self.currentpeak.value = self.hass.states.get(self.currentpeak.entity) if self.hass.states.get(
            self.currentpeak.entity) is not None else 0


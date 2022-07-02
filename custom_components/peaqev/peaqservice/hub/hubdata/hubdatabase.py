import logging
from abc import abstractmethod

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.charger.charger import Charger
from custom_components.peaqev.peaqservice.chargertypes.chargertypes import ChargerTypeData
from custom_components.peaqev.peaqservice.hub.hubmember.chargerswitch import ChargerSwitch
from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import CurrentPeak, HubMember, CarPowerSensor, \
    ChargerObject
from custom_components.peaqev.peaqservice.locale import LocaleData

_LOGGER = logging.getLogger(__name__)


class HubDataBase:
    locale: LocaleData
    chargertype: ChargerTypeData
    currentpeak: CurrentPeak
    carpowersensor: CarPowerSensor
    chargerobject: HubMember
    chargerobject_switch: ChargerSwitch
    hass: HomeAssistant
    charger: Charger

    def create_hub_base_data(
            self,
            hass,
            config_inputs: dict,
            domain: str
    ):
        self.hass = hass

        resultdict = {}

        self.locale = LocaleData(
            config_inputs["locale"],
            domain,
            hass
        )
        self.chargertype = ChargerTypeData(
            hass,
            config_inputs["chargertype"],
            config_inputs["chargerid"]
        )
        self.currentpeak = CurrentPeak(
            data_type=float,
            initval=0,
            startpeaks=config_inputs["startpeaks"],
        )
        self.chargerobject = ChargerObject(
            data_type=self.chargertype.charger.native_chargerstates,
            listenerentity=self.chargertype.charger.entities.chargerentity
        )
        resultdict[self.chargerobject.entity] = self.chargerobject.is_initialized

        self.carpowersensor = CarPowerSensor(
            data_type=int,
            listenerentity=self.chargertype.charger.entities.powermeter,
            powermeter_factor=self.chargertype.charger.options.powermeter_factor,
            hubdata=self
        )

        self.chargerobject_switch = ChargerSwitch(
            hass=hass,
            data_type=bool,
            listenerentity=self.chargertype.charger.entities.powerswitch,
            initval=False,
            currentname=self.chargertype.charger.entities.ampmeter,
            ampmeter_is_attribute=self.chargertype.charger.options.ampmeter_is_attribute,
            hubdata=self
        )
        self.charger = Charger(
            self,
            hass,
            self.chargertype.charger.servicecalls
        )

        _LOGGER.debug(self.chargertype.charger.entities.chargerentity)

    @abstractmethod
    def init_hub_values(self):
        pass

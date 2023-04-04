from abc import abstractmethod
from dataclasses import dataclass, field

from peaqevcore.models.hub.carpowersensor import CarPowerSensor
from peaqevcore.models.hub.chargerobject import ChargerObject
from peaqevcore.models.hub.chargerswitch import ChargerSwitch
from peaqevcore.models.hub.currentpeak import CurrentPeak
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power
from peaqevcore.services.locale.Locale import LocaleData

from custom_components.peaqev.peaqservice.hub.const import CONSUMPTION_TOTAL_NAME, CHARGERDONE, CHARGERENABLED, HOURLY
from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


@dataclass
class IHubSensors:
    charger_enabled: HubMember = field(init=False)
    charger_done: HubMember = field(init=False)
    current_peak: CurrentPeak = field(init=False)
    totalhourlyenergy: HubMember = field(init=False)
    carpowersensor: CarPowerSensor = field(init=False)
    locale: LocaleData = field(init=False)
    chargerobject: ChargerObject = field(init=False)
    chargerobject_switch: ChargerSwitch = field(init=False)
    state_machine: any = field(init=False)
    powersensormovingaverage: HubMember = field(init=False)
    powersensormovingaverage24: HubMember = field(init=False)
    power: Power = field(init=False)

    @abstractmethod
    def setup(self,
              state_machine,
              options: HubOptions,
              domain: str,
              chargerobject: any):
        pass

    def setup_base(
            self,
            options: HubOptions,
            state_machine,
            domain: str,
            chargerobject
    ):
        self.chargertype = chargerobject
        self.state_machine = state_machine
        resultdict = {}

        self.charger_enabled = HubMember(
            data_type=bool,
            listenerentity=f"switch.{domain}_{nametoid(CHARGERENABLED)}",
            initval=False
        )
        if self.chargertype.type.value != "None":
            self.charger_done = HubMember(
                data_type=bool,
                listenerentity=f"binary_sensor.{domain}_{nametoid(CHARGERDONE)}",
                initval=False
            )
        self.locale = LocaleData(
            options.locale,
            domain
        )
        self.current_peak = CurrentPeak(
            data_type=float,
            initval=0,
            startpeaks=options.startpeaks,
        )
        if len(self.chargertype.entities.chargerentity) and self.chargertype.type.value != "None":
            self.chargerobject = ChargerObject(
                data_type=self.chargertype.native_chargerstates,
                listenerentity=self.chargertype.entities.chargerentity
            )
            resultdict[self.chargerobject.entity] = self.chargerobject.is_initialized

            self.carpowersensor = CarPowerSensor(
                data_type=int,
                listenerentity=self.chargertype.entities.powermeter,
                powermeter_factor=self.chargertype.options.powermeter_factor,
                hubdata=self,
                init_override=True
            )
            self.chargerobject_switch = ChargerSwitch(
                hass=state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                currentname=self.chargertype.entities.ampmeter,
                hubdata=self,
                init_override=True
            )

        elif self.chargertype.type.value != "None":
            self.chargerobject = ChargerObject(
                data_type=self.chargertype.native_chargerstates,
                listenerentity="no entity",
                init_override=True
            )
            resultdict[self.chargerobject.entity] = True

            self.carpowersensor = CarPowerSensor(
                data_type=int,
                listenerentity=self.chargertype.entities.powermeter,
                powermeter_factor=self.chargertype.options.powermeter_factor,
                hubdata=self
            )
            self.chargerobject_switch = ChargerSwitch(
                hass=state_machine,
                data_type=bool,
                listenerentity=self.chargertype.entities.powerswitch,
                initval=False,
                currentname=self.chargertype.entities.ampmeter,
                hubdata=self
            )
        self.totalhourlyenergy = HubMember(
            data_type=float,
            listenerentity=f"sensor.{domain}_{nametoid(CONSUMPTION_TOTAL_NAME)}_{HOURLY}",
            initval=0
        )

    def init_hub_values(self):
        """Initialize values from Home Assistant on the set objects"""
        if self.chargertype.type.value != "None":
            if self.chargerobject is not None:
                self.chargerobject.value = self.state_machine.states.get(
                    self.chargerobject.entity).state if self.state_machine.states.get(
                    self.chargerobject.entity) is not None else 0
            self.chargerobject_switch.value = self.state_machine.states.get(
                self.chargerobject_switch.entity).state if self.state_machine.states.get(
                self.chargerobject_switch.entity) is not None else ""
            self.chargerobject_switch.updatecurrent()
            self.carpowersensor.value = self.state_machine.states.get(self.carpowersensor.entity).state if isinstance(
                self.state_machine.states.get(self.carpowersensor.entity), (float, int)) else 0
        self.totalhourlyenergy.value = self.state_machine.states.get(self.totalhourlyenergy.entity) if isinstance(
            self.state_machine.states.get(self.totalhourlyenergy.entity), (float, int)) else 0











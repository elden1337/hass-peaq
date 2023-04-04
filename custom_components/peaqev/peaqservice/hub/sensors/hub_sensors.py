from dataclasses import dataclass

# from ..models.hub.const import CONSUMPTION_TOTAL_NAME, AVERAGECONSUMPTION, AVERAGECONSUMPTION_24H, CHARGERDONE, CHARGERENABLED
from peaqevcore.models.hub.hubmember import HubMember
from peaqevcore.models.hub.power import Power

from custom_components.peaqev.peaqservice.hub.models.hub_options import HubOptions
from custom_components.peaqev.peaqservice.hub.sensors.ihub_sensors import IHubSensors
from custom_components.peaqev.peaqservice.util.extensionmethods import nametoid


@dataclass
class HubSensors(IHubSensors):
    def setup(
            self,
            state_machine,
            options: HubOptions,
            domain: str,
            chargerobject: any):
        super().setup_base(state_machine=state_machine, options=options, domain=domain, chargerobject=chargerobject)

        self.powersensormovingaverage = HubMember(
            data_type=int,
            listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION)}",
            initval=0
        )
        self.powersensormovingaverage24 = HubMember(
            data_type=int,
            listenerentity=f"sensor.{domain}_{nametoid(AVERAGECONSUMPTION_24H)}",
            initval=0
        )

        self.power = Power(
            configsensor=options.powersensor,
            powersensor_includes_car=options.powersensor_includes_car
        )
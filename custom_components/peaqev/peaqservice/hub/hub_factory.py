from homeassistant.core import HomeAssistant
from peaqevcore.common.models.peaq_system import PeaqSystem
from peaqevcore.common.spotprice.spotprice_factory import SpotPriceFactory
from peaqevcore.services.prediction.prediction import Prediction

from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller_factory import \
    ChargeControllerFactory
from custom_components.peaqev.peaqservice.chargertypes.chargertype_factory import \
    ChargerTypeFactory
from custom_components.peaqev.peaqservice.hub.factories.hourselection_factory import \
    HourselectionFactory
from custom_components.peaqev.peaqservice.hub.factories.threshold_factory import \
    ThresholdFactory
from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub
from custom_components.peaqev.peaqservice.hub.hub_events import HubEvents
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.observer.iobserver_coordinator import \
    IObserver
from custom_components.peaqev.peaqservice.hub.observer.observer_coordinator import \
    Observer
from custom_components.peaqev.peaqservice.hub.price_aware_hub import \
    PriceAwareHub
from custom_components.peaqev.peaqservice.hub.sensors.hubsensors_factory import \
    HubSensorsFactory
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes_factory import \
    StateChangesFactory
from custom_components.peaqev.peaqservice.powertools.powertools_factory import \
    PowerToolsFactory


class HubFactory:
    @staticmethod
    async def async_create(hass: HomeAssistant, options: HubOptions, domain: str) -> HomeAssistantHub:
        observer = Observer(hass)
        if options.price.price_aware:
            hub = PriceAwareHub
        else:
            hub = HomeAssistantHub
        return await HubFactory.async_setup(hub(hass, options, domain, observer), observer)

    @staticmethod
    async def async_setup(hub: HomeAssistantHub, observer: IObserver) -> HomeAssistantHub:
        hub.chargertype = await ChargerTypeFactory.async_create(hub.state_machine, hub.options)
        hub.sensors = await HubSensorsFactory.async_create(hub=hub)
        hub.chargecontroller = await ChargeControllerFactory.async_create(
            hub=hub,
            observer=observer,
            charger_states=hub.chargertype.chargerstates,
            charger_type=hub.chargertype.type,
        )
        hub.hours = await HourselectionFactory.async_create(hub)
        hub.threshold = await ThresholdFactory.async_create(hub)
        hub.prediction = Prediction(hub)
        hub.servicecalls = ServiceCalls(hub, observer)
        hub.states = await StateChangesFactory.async_create(hub)
        hub.spotprice = SpotPriceFactory.create(
            hub=hub,
            observer=observer,
            system=PeaqSystem.PeaqEv,
            test=False,
            is_active=hub.options.price.price_aware,
            custom_sensor=hub.options.price.custom_sensor,
            spotprice_type=hub.options.price.spotprice_type,
        )
        hub.power = await PowerToolsFactory.async_create(hub, observer)
        hub.events = HubEvents(hub, hub.state_machine)
        return hub

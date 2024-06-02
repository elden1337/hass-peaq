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
from custom_components.peaqev.peaqservice.hub.max_min_controller import MaxMinController
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions
from custom_components.peaqev.peaqservice.hub.price_aware_hub import \
    PriceAwareHub
from custom_components.peaqev.peaqservice.hub.sensors.hubsensors_factory import \
    HubSensorsFactory
from custom_components.peaqev.peaqservice.hub.servicecalls import ServiceCalls
from custom_components.peaqev.peaqservice.hub.state_changes.state_changes_factory import \
    StateChangesFactory
from custom_components.peaqev.peaqservice.observer.iobserver_coordinator import IObserver
from custom_components.peaqev.peaqservice.observer.observer_coordinator import Observer
from custom_components.peaqev.peaqservice.powertools.powertools_factory import \
    PowerToolsFactory
from custom_components.peaqev.peaqservice.util.HomeAssistantFacade import IHomeAssistantFacade
from custom_components.peaqev.peaqservice.util.schedule_options_handler import SchedulerOptionsHandler


class HubFactory:
    @staticmethod
    async def async_create(hass: IHomeAssistantFacade, options: HubOptions, domain: str) -> HomeAssistantHub:
        observer = Observer(hass)

        if options.price.price_aware:
            hub = PriceAwareHub(
                hass,
                options,
                domain,
                observer,
                MaxMinController(
                    options,
                    observer,
                    hass,
                    options.max_charge
                ),
None
            )
            scheduler_options_handler = SchedulerOptionsHandler(hub, hass) #todo: move to hub constructor
            hub.scheduler_options_handler = scheduler_options_handler #todo: remove when redundant
        else:
            hub = HomeAssistantHub(hass, options, domain, observer, None, None)

        return await HubFactory.async_setup(hub, observer, hass)

    @staticmethod
    async def async_setup(hub: HomeAssistantHub, observer: IObserver, state_machine: IHomeAssistantFacade) -> HomeAssistantHub:
        chargertype = await ChargerTypeFactory.async_create(hub.state_machine, hub.options)
        hub.chargertype = chargertype
        hub.sensors = await HubSensorsFactory.async_create(
            state_machine,
            hub.options,
            hub.model.domain,
            chargertype
        )
        hub.chargecontroller = await ChargeControllerFactory.async_create(
            hub,
            charger_states=chargertype.chargerstates,
            charger_type=chargertype.type,
            observer=observer
        )
        hub.hours = await HourselectionFactory.async_create(hub)
        hub.threshold = await ThresholdFactory.async_create(hub)
        hub.prediction = Prediction(hub)  # threshold
        hub.servicecalls = ServiceCalls(hub)  # top level
        hub.states = await StateChangesFactory.async_create(hub)  # top level
        hub.spotprice = SpotPriceFactory.create(
            hub=hub,
            observer=observer,
            system=PeaqSystem.PeaqEv,
            test=False,
            is_active=hub.options.price.price_aware,
            custom_sensor=hub.options.price.custom_sensor
        )
        hub.power = await PowerToolsFactory.async_create(hub, observer, state_machine) #todo: remove hub from here
        hub.events = HubEvents(observer, state_machine)
        return hub

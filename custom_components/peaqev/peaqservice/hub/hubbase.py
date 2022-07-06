import logging
from abc import abstractmethod
from datetime import datetime

from homeassistant.core import (
    HomeAssistant,
    callback,
)

import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.hourselection import (PriceAwareHours, RegularHours)
from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import HubMember
from custom_components.peaqev.peaqservice.hub.scheduler.schedule import Scheduler
from custom_components.peaqev.peaqservice.util.constants import CHARGERENABLED, CHARGERDONE
from custom_components.peaqev.peaqservice.util.timer import Timer

_LOGGER = logging.getLogger(__name__)


class HubBase:
    """This is the shared baseclass for regular hub and hublite"""
    hub_id = 1337

    def __init__(
            self,
            hass: HomeAssistant,
            config_inputs: dict,
            domain: str
    ):
        self.hass = hass
        self.hubname = domain.capitalize()
        self.domain = domain
        self.price_aware = config_inputs["priceaware"]
        self.peaqtype_is_lite = config_inputs["peaqtype_is_lite"]
        self.timer = Timer()

        if self.price_aware is True:
            self.hours = PriceAwareHours(
                hass=self.hass,
                absolute_top_price=config_inputs["absolute_top_price"],
                cautionhour_type=config_inputs["cautionhour_type"],
                min_price=config_inputs["min_price"],
                hub=self,
                allow_top_up=config_inputs["allow_top_up"]
            )
        else:
            self.hours = RegularHours(
                non_hours=config_inputs["nonhours"],
                caution_hours=config_inputs["cautionhours"]
            )

        self.charger_enabled = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(CHARGERENABLED)}",
            initval=config_inputs["behavior_on_default"]
        )
        self.charger_done = HubMember(
            data_type=bool,
            listenerentity=f"binary_sensor.{domain}_{ex.nametoid(CHARGERDONE)}",
            initval=False
        )
        self.scheduler = Scheduler(hub=self)

    @property
    def non_hours(self) -> list:
        return self.scheduler.non_hours if self.scheduler.scheduler_active else self.hours.non_hours

    @property
    def dynamic_caution_hours(self) -> dict:
        return self.scheduler.caution_hours if self.scheduler.scheduler_active else self.hours.dynamic_caution_hours

    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @callback
    async def state_changed(self, entity_id, old_state, new_state):
        try:
            if old_state is None or old_state.state != new_state.state:
                await self._update_sensor(entity_id, new_state.state)
        except Exception as e:
            msg = f"Unable to handle data: {entity_id} ({e})"
            _LOGGER.error(msg)

    @abstractmethod
    async def _update_sensor(self, entity, value):
        pass

    async def call_enable_peaq(self):
        """peaqev.enable"""
        self.charger_enabled.value = True
        self.charger_done.value = False

    async def call_disable_peaq(self):
        """peaqev.disable"""
        self.charger_enabled.value = False
        self.charger_done.value = False

    async def call_override_nonhours(self, hours:int=1):
        """peaqev.override_nonhours"""
        self.timer.update(hours)

    async def call_schedule_needed_charge(
            self,
            charge_amount:float,
            departure_time:str,
            schedule_starttime:str = None,
            override_settings:bool = False
        ):
        dep_time = datetime.strptime(departure_time, '%y-%m-%d %H:%M')
        if schedule_starttime is not None:
            start_time = datetime.strptime(schedule_starttime, '%y-%m-%d %H:%M')
        else:
            start_time = datetime.now()
        _LOGGER.debug(f"scheduler params. charge: {charge_amount}, dep-time: {dep_time}, start_time: {start_time}")
        self.scheduler.create_schedule(charge_amount, dep_time, start_time, override_settings)

    async def call_scheduler_cancel(self):
        self.scheduler.cancel()

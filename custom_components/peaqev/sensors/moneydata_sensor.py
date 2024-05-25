from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.hub import HomeAssistantHub

from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.peaqev.peaqservice.hub.const import (
    AVERAGE_SPOTPRICE_DATA, LookupKeys)
from custom_components.peaqev.sensors.money_sensor_helpers import *
from custom_components.peaqev.sensors.sensorbase import MoneyDevice

_LOGGER = logging.getLogger(__name__)


class MoneyDataSensor(MoneyDevice, RestoreEntity):
    """Holding spotprice average data"""

    def __init__(self, hub: HomeAssistantHub, entry_id):
        name = f'{hub.hubname} {AVERAGE_SPOTPRICE_DATA}'
        super().__init__(hub, name, entry_id)

        self._attr_name = name
        self._state = None
        self._average_spotprice_data = {}
        self._average_stdev_data = {}

    @property
    def state(self) -> str:
        return self._state.strftime('%Y-%m-%d %H:%M:%S') if self._state else 'off'

    @property
    def icon(self) -> str:
        return 'mdi:database-outline'

    async def async_update(self) -> None:
            ret = await self.hub.async_request_sensor_data(LookupKeys.AVERAGE_SPOTPRICE_DATA, LookupKeys.AVERAGE_STDEV_DATA)
            if ret is not None:
                if len(ret):
                    incoming_prices = ret.get(LookupKeys.AVERAGE_SPOTPRICE_DATA, {})
                    incoming_stdev = ret.get(LookupKeys.AVERAGE_STDEV_DATA, {})

                    if incoming_prices != self._average_spotprice_data or self._state < datetime.now()+timedelta(minutes=-30):
                        self._state = datetime.now()
                        _diff = self.diff_dicts(self._average_spotprice_data, incoming_prices)
                        if len(_diff[0]) or len(_diff[1]):
                            _LOGGER.debug(f'dict avgprice was changed: added: {_diff[0]}, removed: {_diff[1]}')
                    self._average_spotprice_data = incoming_prices

                    if incoming_stdev != self._average_stdev_data:
                        _diff = self.diff_dicts(self._average_stdev_data, incoming_stdev)
                        if len(_diff[0]) or len(_diff[1]):
                            _LOGGER.debug(f'dict stdev was changed: added: {_diff[0]}, removed: {_diff[1]}')
                    self._average_stdev_data = incoming_stdev

    @staticmethod
    def diff_dicts(dict1, dict2):
        """Just a helper to debuglog if there has been changes so we know what it's doing."""
        added = {key: dict2[key] for key in dict2 if key not in dict1}
        removed = {key: dict1[key] for key in dict1 if key not in dict2}
        return added, removed

    @property
    def extra_state_attributes(self) -> dict:
        attr_dict = {
            'Spotprice average data':   self._average_spotprice_data,
            'Spotprice stdev data': self._average_stdev_data
        }
        return attr_dict

    async def async_added_to_hass(self):
        state = await super().async_get_last_state()
        _LOGGER.debug('last state of %s = %s', self._attr_name, state)
        if state:
            self._state = datetime.now()
            data = state.attributes.get('Spotprice average data', {})
            stdev = state.attributes.get('Spotprice stdev data', {})
            if len(data):
                try:
                    await self.hub.spotprice.async_import_average_data(incoming_prices=data, incoming_stdev=stdev)
                except Exception as e:
                    _LOGGER.error(f'Unable to import average data from state. {e}')
                    _LOGGER.debug(f'Data: {data}')
                    _LOGGER.debug(f'Stdev: {stdev}')

                self._average_spotprice_data = self.hub.spotprice.average_data
                self._average_stdev_data = self.hub.spotprice.average_stdev_data

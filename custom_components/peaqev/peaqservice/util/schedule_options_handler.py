from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.peaqev.peaqservice.hub.price_aware_hub import PriceAwareHub

TODAYAT = 'Today at'
TOMORROWAT = 'Tomorrow at'
NOSCHEDULE = 'No schedule'

_LOGGER = logging.getLogger(__name__)

class SchedulerOptionsHandler:
    def __init__(self, hub):
        self.hub: PriceAwareHub = hub

    @property
    def display_options(self) -> list[str]:
        ret = SchedulerOptionsHandler.convert_datetime_list(self.options)
        ret.insert(0, NOSCHEDULE)
        return ret

    @property
    def options(self) -> list[datetime]:
        now = datetime.now()
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=3))
        end_time = (now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2))
        options = []
        while next_hour <= end_time:
            options.append(next_hour)
            next_hour += timedelta(hours=1)
        return options

    @options.setter
    def options(self, values: list[datetime]):
        pass

    async def async_handle_scheduler_departure_option(self, option: str):
        try:
            converted_option = SchedulerOptionsHandler.reverse_convert_string(option)
            if converted_option is None:
                _LOGGER.info('Cancelling scheduler service')
                await self.hub.servicecalls.async_call_scheduler_cancel()
                return

            _LOGGER.info('Calling scheduler service with', converted_option)
            await self.hub.servicecalls.async_call_schedule_needed_charge(
                charge_amount=self.hub.max_min_controller.max_charge,
                departure_time=converted_option.strftime('%Y-%m-%d %H:%M'),
                override_settings=False,
            )
        except ValueError as v:
            _LOGGER.error(f'Unable to convert option {option}. {v}')

    @staticmethod
    def convert_datetime_list(dates_list):
        result = []
        for value in dates_list:
            if value.date() == datetime.now().date():
                result.append(f'{TODAYAT} {value.hour}')
            elif value.date() == (datetime.now().date() + timedelta(days=1)):
                result.append(f'{TOMORROWAT} {value.hour}')
            else:
                result.append(value.strftime('%B %d at %H'))
        return result

    @staticmethod
    def reverse_convert_string(string_val):
        if string_val == NOSCHEDULE:
            return None
        if string_val.startswith(TODAYAT):
            hour = int(string_val.split(' ')[-1])
            return datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        elif string_val.startswith(TOMORROWAT):
            hour = int(string_val.split(' ')[-1])
            return (datetime.now() + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
        else:
            match = re.match(r'(\w+) (\d+) at (\d+)', string_val)
            if match:
                month, day, hour = match.groups()
                return datetime.strptime(f'{month} {day} {hour}', '%B %d %H')

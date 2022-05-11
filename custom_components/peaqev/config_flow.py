"""Config flow for Peaq integration."""
from __future__ import annotations
import logging
import voluptuous as vol
from typing import Any, Optional
from homeassistant import config_entries
from homeassistant.core import (HomeAssistant)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.peaqev.peaqservice.util.constants as pk

from .const import DOMAIN   # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)



LITE_SCHEMA = vol.Schema(
    {
        vol.Required(
            "peaqevtype",
            default="",
        ): vol.In(pk.INSTALLATIONTYPES)
    }
)

INIT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional("powersensorincludescar", default=False): cv.boolean, 
        vol.Optional(
            "chargertype",
            default="",
            ): vol.In(pk.CHARGERTYPES),
        vol.Optional("chargerid"): cv.string,
        vol.Optional(
            "locale",
            default="",
            ): vol.In(pk.LOCALES)
    }
)

async def _check_power_sensor(hass: HomeAssistant, powersensor:str) -> bool:
    ret = hass.states.get(powersensor).state
    try:
        float(ret)
        return True
    except:
        msg = f"{powersensor} did not produce a valid state for {DOMAIN}. State was {ret}"
        _LOGGER.error(msg)
        return False


async def _validate_input_first(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """ Validate the data can be used to set up a connection."""

    if len(data["chargerid"]) < 3:
        raise ValueError

    if len(data["name"]) < 3:
        raise ValueError
    elif not data["name"].startswith("sensor."):
        data["name"] = f"sensor.{data['name']}"
    #if await _check_power_sensor(hass, data["name"]) is False:
    #    raise ValueError

    return {"title": data["name"]}


async def _validate_input_first_chargerid(data: dict) -> dict[str, Any]:
    """ Validate the chargerId"""
    if len(data["chargerid"]) < 1:
        raise ValueError

    return {"title": data["name"]}


# async def _validate_nonhours(data: dict) -> dict[str, Any]:
#     """ Validate nonhour-length"""
#     if len(data["nonhours"]) == 24:
#         raise ValueError

#     return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                self.info = await _validate_input_first(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_powersensor"
            try:
                self.info = await _validate_input_first_chargerid(user_input)
            except ValueError:
                errors["base"] = "invalid_chargerid"
            if not errors:
                self.data = user_input
                #self.data[self.OPTIONS] = []
                return await self.async_step_hours()
                #return self.async_create_entry(title=self.info["title"], data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=INIT_SCHEMA, errors=errors,last_step=False
        )

    async def async_step_hours(self, user_input=None):
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_months()

        mockhours = [h for h in range(0, 24)]

        _transfer_cautionhours = mockhours
        _transfer_nonhours = mockhours
        _priceaware = False
        _absolute_top_price = 0
        _cautionhour_type = pk.CAUTIONHOURTYPE_INTERMEDIATE

        return self.async_show_form(
            step_id="hours",
            data_schema=vol.Schema(
            {
                vol.Optional("nonhours", default=list(_transfer_nonhours)): cv.multi_select(
                    mockhours
                ),
                vol.Optional("cautionhours", default=list(_transfer_cautionhours)): cv.multi_select(
                    mockhours
                ),
                vol.Optional("priceaware", default=_priceaware): cv.boolean,
                vol.Optional("absolute_top_price", default=_absolute_top_price): cv.positive_float,
                vol.Optional(
                    "cautionhour_type",
                    default=pk.CAUTIONHOURTYPE_INTERMEDIATE,
                ): vol.In(pk.CAUTIONHOURTYPE_NAMES),
            }),
            last_step=False,
        )

    async def async_step_months(self, user_input=None):
        if user_input is not None:
            months_dict = await _set_startpeak_dict(user_input)
            self.data["startpeaks"] = months_dict
            return self.async_create_entry(title=self.info["title"], data=self.data)

        months = [m for m in range(1, 13)]

        mock_startpeaks = {}
        for m in months:
            _m = str(m)
            mock_startpeaks[_m] = 1.5

        _transfer_startpeaks = mock_startpeaks

        return self.async_show_form(
            step_id="months",
            data_schema=vol.Schema(
                {
                vol.Optional("jan", default=_transfer_startpeaks["1"]): cv.positive_float,
                vol.Optional("feb", default=_transfer_startpeaks["2"]): cv.positive_float,
                vol.Optional("mar", default=_transfer_startpeaks["3"]): cv.positive_float,
                vol.Optional("apr", default=_transfer_startpeaks["4"]): cv.positive_float,
                vol.Optional("may", default=_transfer_startpeaks["5"]): cv.positive_float,
                vol.Optional("jun", default=_transfer_startpeaks["6"]): cv.positive_float,
                vol.Optional("jul", default=_transfer_startpeaks["7"]): cv.positive_float,
                vol.Optional("aug", default=_transfer_startpeaks["8"]): cv.positive_float,
                vol.Optional("sep", default=_transfer_startpeaks["9"]): cv.positive_float,
                vol.Optional("oct", default=_transfer_startpeaks["10"]): cv.positive_float,
                vol.Optional("nov", default=_transfer_startpeaks["11"]): cv.positive_float,
                vol.Optional("dec", default=_transfer_startpeaks["12"]): cv.positive_float
                }),
            last_step=True,
        )

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)

# class OptionsFlowHandler(config_entries.OptionsFlow):
#
#     def __init__(self, config_entry):
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)
#
#     async def async_step_init(self, user_input=None):
#         return await self.async_step_hours()
#
#     async def async_step_hours(self, user_input=None):
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self.async_step_startpeaks()
#
#         mockhours = [h for h in range(0, 24)]
#
#         _transfer_cautionhours = self.config_entry.options["cautionhours"] if "cautionhours" in self.config_entry.options.keys() else self.config_entry.data["options"]["cautionhours"] if "cautionhours" in self.config_entry.data["options"].keys() else mockhours
#         _transfer_nonhours = self.config_entry.options["nonhours"] if "nonhours" in self.config_entry.options.keys() else self.config_entry.data["options"]["nonhours"] if "nonhours" in self.config_entry.data["options"].keys() else mockhours
#         _priceaware = self.config_entry.options["priceaware"] if "priceaware" in self.config_entry.options.keys() else False
#         _absolute_top_price = self.config_entry.options["absolute_top_price"] if "absolute_top_price" in self.config_entry.options.keys() else None
#         _cautionhour_type = self.config_entry.options["cautionhour_type"] if "cautionhour_type" in self.config_entry.options.keys() else pk.CAUTIONHOURTYPE_INTERMEDIATE
#
#         return self.async_show_form(
#             step_id="hours",
#             data_schema=vol.Schema(
#             {
#                 vol.Optional("nonhours", default=list(_transfer_nonhours)): cv.multi_select(
#                     mockhours
#                 ),
#                 vol.Optional("cautionhours", default=list(_transfer_cautionhours)): cv.multi_select(
#                     mockhours
#                 ),
#                 vol.Optional("priceaware", default=_priceaware): cv.boolean,
#                 vol.Optional("absolute_top_price", default=_absolute_top_price): cv.positive_float,
#                 vol.Optional(
#                     "cautionhour_type",
#                     default=pk.CAUTIONHOURTYPE_INTERMEDIATE,
#                 ): vol.In(pk.CAUTIONHOURTYPE_NAMES),
#             }),
#             last_step=False,
#         )
#
#     async def async_step_startpeaks(self, user_input=None):
#         if user_input is not None:
#             months = await OptionsFlowHandler._set_startpeak_dict(user_input)
#             self.options.update(months)
#             return await self._update_options()
#
#         months = [m for m in range(1, 13)]
#
#         mock_startpeaks = {}
#         for m in months:
#             _m = str(m)
#             mock_startpeaks[_m] = 1.5
#
#         _transfer_startpeaks = self.config_entry.options["startpeaks"] if "startpeaks" in self.config_entry.options.keys() else self.config_entry.data["options"]["startpeaks"] if "startpeaks" in self.config_entry.data["options"].keys() else mock_startpeaks
#
#         return self.async_show_form(
#             step_id="startpeaks",
#             data_schema=vol.Schema(
#                 {
#                 vol.Optional("jan", default=_transfer_startpeaks["1"]): cv.positive_float,
#                 vol.Optional("feb", default=_transfer_startpeaks["2"]): cv.positive_float,
#                 vol.Optional("mar", default=_transfer_startpeaks["3"]): cv.positive_float,
#                 vol.Optional("apr", default=_transfer_startpeaks["4"]): cv.positive_float,
#                 vol.Optional("may", default=_transfer_startpeaks["5"]): cv.positive_float,
#                 vol.Optional("jun", default=_transfer_startpeaks["6"]): cv.positive_float,
#                 vol.Optional("jul", default=_transfer_startpeaks["7"]): cv.positive_float,
#                 vol.Optional("aug", default=_transfer_startpeaks["8"]): cv.positive_float,
#                 vol.Optional("sep", default=_transfer_startpeaks["9"]): cv.positive_float,
#                 vol.Optional("oct", default=_transfer_startpeaks["10"]): cv.positive_float,
#                 vol.Optional("nov", default=_transfer_startpeaks["11"]): cv.positive_float,
#                 vol.Optional("dec", default=_transfer_startpeaks["12"]): cv.positive_float
#                 }),
#             last_step=True,
#         )
#
#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(title="", data=self.options)


async def _set_startpeak_dict(user_input) -> dict:
    return {1: user_input["jan"], 2: user_input["feb"], 3: user_input["mar"], 4: user_input["apr"],
           5: user_input["may"], 6: user_input["jun"], 7: user_input["jul"], 8: user_input["aug"],
           9: user_input["sep"], 10: user_input["oct"], 11: user_input["nov"], 12: user_input["dec"]}

"""Config flow for Peaq integration."""
from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from typing import Any, Optional

import custom_components.peaqev.peaqservice.util.constants as pk
from custom_components.peaqev.configflow.config_flow_helpers import set_startpeak_dict
from custom_components.peaqev.configflow.config_flow_schemas import (
    SENSOR_SCHEMA,
    PRICEAWARE_SCHEMA,
    HOURS_SCHEMA,
    MONTHS_SCHEMA,
    CHARGER_SCHEMA,
    TYPE_SCHEMA
)
from custom_components.peaqev.configflow.config_flow_validation import ConfigFlowValidation, FaultyPowerSensor
from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""
        errors = {}
        if user_input is not None:
            self.data = user_input
            if self.data["peaqevtype"] == pk.TYPELITE:
                self.info = {"title": pk.TYPELITE}
                return await self.async_step_charger()
            return await self.async_step_sensor()

        return self.async_show_form(
            step_id="user",
            data_schema=TYPE_SCHEMA,
            errors=errors,
            last_step=False
        )

    async def async_step_sensor(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                self.info = await ConfigFlowValidation.validate_input_first(user_input)
                # await ConfigFlowValidation.validate_power_sensor(self.hass, user_input["powersensor"])
            except ValueError:
                errors["base"] = "invalid_powersensor"
            if not errors:
                self.data.update(user_input)
            return await self.async_step_charger()

        return self.async_show_form(
            step_id="sensor",
            data_schema=SENSOR_SCHEMA,
            errors=errors,
            last_step=False
        )

    async def async_step_charger(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                self.data.update(user_input)
                return await self.async_step_priceaware()
            except FaultyPowerSensor:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="charger",
            data_schema=CHARGER_SCHEMA,
            errors=errors,
            last_step=False
        )

    async def async_step_priceaware(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data.update(user_input)
            if self.data["priceaware"] is False:
                return await self.async_step_hours()
            return await self.async_step_months()

        return self.async_show_form(
            step_id="priceaware",
            data_schema=PRICEAWARE_SCHEMA,
            errors=errors,
            last_step=False,
        )

    async def async_step_hours(self, user_input=None):
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_months()

        return self.async_show_form(
            step_id="hours",
            data_schema=HOURS_SCHEMA,
            last_step=False,
        )

    async def async_step_months(self, user_input=None):
        if user_input is not None:
            months_dict = await set_startpeak_dict(user_input)
            self.data["startpeaks"] = months_dict
            return self.async_create_entry(title=self.info["title"], data=self.data)

        return self.async_show_form(
            step_id="months",
            data_schema=MONTHS_SCHEMA,
            last_step=True,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def _get_existing_param(self, parameter: str, default_val: any):
        if parameter in self.config_entry.options.keys():
            return self.config_entry.options.get(parameter)
        if parameter in self.config_entry.data.keys():
            return self.config_entry.data.get(parameter)
        return default_val

    async def async_step_init(self, user_input=None):
        """Priceaware"""
        if user_input is not None:
            self.options.update(user_input)
            if self.options["priceaware"] is False:
                return await self.async_step_hours()
            return await self.async_step_months()

        _priceaware = await self._get_existing_param("priceaware", False)
        _topprice = await self._get_existing_param("absolute_top_price", 0)
        _minprice = await self._get_existing_param("min_priceaware_threshold_price", 0)
        _hourtype = await self._get_existing_param("cautionhour_type", pk.CAUTIONHOURTYPE_INTERMEDIATE)
        _allow_top_up = await self._get_existing_param("allow_top_up", False)

        return self.async_show_form(
            step_id="init",
            last_step=False,
            data_schema=vol.Schema(
                {
                    vol.Optional("priceaware", default=_priceaware): cv.boolean,
                    vol.Optional("allow_top_up", default=_allow_top_up): cv.boolean,
                    vol.Optional("absolute_top_price", default=_topprice): cv.positive_float,
                    vol.Optional("min_priceaware_threshold_price", default=_minprice): cv.positive_float,
                    vol.Optional(
                        "cautionhour_type",
                        default=_hourtype,
                    ): vol.In(pk.CAUTIONHOURTYPE_NAMES),
                }),
        )

    async def async_step_hours(self, user_input=None):
        """Hours"""
        if user_input is not None:
            self.options.update(user_input)
            return await self.async_step_months()

        _nonhours = await self._get_existing_param("nonhours", list(range(0, 24)))
        _cautionhours = await self._get_existing_param("cautionhours", list(range(0, 24)))

        return self.async_show_form(
            step_id="hours",
            last_step=False,
            data_schema=vol.Schema(
            {
                vol.Optional("nonhours", default=_nonhours): cv.multi_select(
                    list(range(0, 24))
                ),
                vol.Optional("cautionhours", default=_cautionhours): cv.multi_select(
                    list(range(0, 24))
                )
            }),
        )

    async def async_step_months(self, user_input=None):
        """Months"""
        if user_input is not None:
            months_dict = await set_startpeak_dict(user_input)
            self.options["startpeaks"] = months_dict
            return await self.async_step_misc()
            #return self.async_create_entry(title="", data=self.options)

        defaultvalues = self.config_entry.options.get(
            "startpeaks") if "startpeaks" in self.config_entry.options.keys() else self.config_entry.data.get(
            "startpeaks")

        return self.async_show_form(
            step_id="months",
            last_step=False,
            data_schema=vol.Schema(
                {
                    vol.Optional("jan", default=defaultvalues["1"]): cv.positive_float,
                    vol.Optional("feb", default=defaultvalues["2"]): cv.positive_float,
                    vol.Optional("mar", default=defaultvalues["3"]): cv.positive_float,
                    vol.Optional("apr", default=defaultvalues["4"]): cv.positive_float,
                    vol.Optional("may", default=defaultvalues["5"]): cv.positive_float,
                    vol.Optional("jun", default=defaultvalues["6"]): cv.positive_float,
                    vol.Optional("jul", default=defaultvalues["7"]): cv.positive_float,
                    vol.Optional("aug", default=defaultvalues["8"]): cv.positive_float,
                    vol.Optional("sep", default=defaultvalues["9"]): cv.positive_float,
                    vol.Optional("oct", default=defaultvalues["10"]): cv.positive_float,
                    vol.Optional("nov", default=defaultvalues["11"]): cv.positive_float,
                    vol.Optional("dec", default=defaultvalues["12"]): cv.positive_float
                })
        )

    async def async_step_misc(self, user_input=None):
        """Misc"""
        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(title="", data=self.options)

        _behavior_on_default = self.config_entry.options.get(
            "behavior_on_default") if "behavior_on_default" in self.config_entry.options.keys() else False

        return self.async_show_form(
            step_id="misc",
            last_step=True,
            data_schema=vol.Schema(
                {
                    vol.Optional("behavior_on_default", default=_behavior_on_default): cv.boolean
                })
        )

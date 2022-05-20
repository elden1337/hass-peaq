"""Config flow for Peaq integration."""
from __future__ import annotations

import logging
from config_flow.config_flow_schemas import (
    SENSOR_SCHEMA,
    PRICEAWARE_SCHEMA,
    HOURS_SCHEMA,
    MONTHS_SCHEMA,
    CHARGER_SCHEMA,
    TYPE_SCHEMA
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from typing import Any, Optional
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
import custom_components.peaqev.peaqservice.util.constants as pk
from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


async def _set_startpeak_dict(user_input) -> dict:
    return {1: user_input["jan"], 2: user_input["feb"], 3: user_input["mar"], 4: user_input["apr"],
           5: user_input["may"], 6: user_input["jun"], 7: user_input["jul"], 8: user_input["aug"],
           9: user_input["sep"], 10: user_input["oct"], 11: user_input["nov"], 12: user_input["dec"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

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
                self.info = await _validate_input_first(user_input)
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
            #try:
            #    self.info = await _validate_input_first_chargerid(user_input)
            #except ValueError:
            #    errors["base"] = "invalid_chargerid"
            #if not errors:
            self.data.update(user_input)
            return await self.async_step_priceaware()

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

        _priceaware = False
        _absolute_top_price = 0

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

        mockhours = list(range(0,24))

        _transfer_cautionhours = mockhours
        _transfer_nonhours = mockhours

        return self.async_show_form(
            step_id="hours",
            data_schema=HOURS_SCHEMA,
            last_step=False,
        )

    async def async_step_months(self, user_input=None):
        if user_input is not None:
            months_dict = await _set_startpeak_dict(user_input)
            self.data["startpeaks"] = months_dict
            return self.async_create_entry(title=self.info["title"], data=self.data)

        months = list(range(1,13))

        mock_startpeaks = {}
        for m in months:
            _m = str(m)
            mock_startpeaks[_m] = 1.5

        _transfer_startpeaks = mock_startpeaks

        return self.async_show_form(
            step_id="months",
            data_schema=MONTHS_SCHEMA,
            last_step=True,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}
        # Grab all configured repos from the entity registry so we can populate the
        # multi-select dropdown that will allow a user to remove a repo.
        entity_registry = await async_get_registry(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        # Default value for our multi-select.
        all_repos = {e.entity_id: e.original_name for e in entries}
        repo_map = {e.entity_id: e for e in entries}

        if user_input is not None:
            updated_repos = deepcopy(self.config_entry.data[CONF_REPOS])

            # Remove any unchecked repos.
            removed_entities = [
                entity_id
                for entity_id in repo_map.keys()
                if entity_id not in user_input["repos"]
            ]
            for entity_id in removed_entities:
                # Unregister from HA
                entity_registry.async_remove(entity_id)
                # Remove from our configured repos.
                entry = repo_map[entity_id]
                entry_path = entry.unique_id
                updated_repos = [e for e in updated_repos if e["path"] != entry_path]

            if user_input.get(CONF_PATH):
                # Validate the path.
                access_token = self.hass.data[DOMAIN][self.config_entry.entry_id][
                    CONF_ACCESS_TOKEN
                ]
                try:
                    await validate_path(user_input[CONF_PATH], access_token, self.hass)
                except ValueError:
                    errors["base"] = "invalid_path"

                if not errors:
                    # Add the new repo.
                    updated_repos.append(
                        {
                            "path": user_input[CONF_PATH],
                            "name": user_input.get(CONF_NAME, user_input[CONF_PATH]),
                        }
                    )

            if not errors:
                # Value of data will be set on the options property of our config_entry
                # instance.
                return self.async_create_entry(
                    title="",
                    data={CONF_REPOS: updated_repos},
                )

        options_schema = vol.Schema(
            {
                vol.Optional("repos", default=list(all_repos.keys())): cv.multi_select(
                    all_repos
                ),
                vol.Optional(CONF_PATH): cv.string,
                vol.Optional(CONF_NAME): cv.string,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
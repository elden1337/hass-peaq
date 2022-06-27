import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME
from peaqevcore.locale_service.Locale import LOCALES

import custom_components.peaqev.peaqservice.util.constants as pk

TYPE_SCHEMA = vol.Schema(
                {
                    vol.Optional(
                        "peaqevtype",
                        default="",
                    ): vol.In(pk.INSTALLATIONTYPES)
                }
            )

SENSOR_SCHEMA = vol.Schema(
                {
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Optional("powersensorincludescar", default=False): cv.boolean
                }
            )

CHARGER_SCHEMA = vol.Schema(
                {
                    vol.Optional(
                        "chargertype",
                        default="",
                        ): vol.In(pk.CHARGERTYPES),
                    vol.Optional("chargerid"): cv.string,
                    vol.Optional(
                        "locale",
                        default="",
                        ): vol.In(LOCALES)
                }
            )

HOURS_SCHEMA = vol.Schema(
            {
                vol.Optional("nonhours"): cv.multi_select(
                    list(range(0, 24))
                ),
                vol.Optional("cautionhours"): cv.multi_select(
                    list(range(0, 24))
                )
            })

PRICEAWARE_SCHEMA = vol.Schema(
                {
                    vol.Optional("priceaware", default=False): cv.boolean,
                    vol.Optional("allow_top_up", default=False): cv.boolean,
                    vol.Optional("absolute_top_price"): cv.positive_float,
                    vol.Optional("min_priceaware_threshold_price"): cv.positive_float,
                    vol.Optional(
                        "cautionhour_type",
                        default=pk.CAUTIONHOURTYPE_INTERMEDIATE,
                    ): vol.In(pk.CAUTIONHOURTYPE_NAMES),
                })

MONTHS_SCHEMA = vol.Schema(
                {
                    vol.Optional("jan", default=1.5): cv.positive_float,
                    vol.Optional("feb", default=1.5): cv.positive_float,
                    vol.Optional("mar", default=1.5): cv.positive_float,
                    vol.Optional("apr", default=1.5): cv.positive_float,
                    vol.Optional("may", default=1.5): cv.positive_float,
                    vol.Optional("jun", default=1.5): cv.positive_float,
                    vol.Optional("jul", default=1.5): cv.positive_float,
                    vol.Optional("aug", default=1.5): cv.positive_float,
                    vol.Optional("sep", default=1.5): cv.positive_float,
                    vol.Optional("oct", default=1.5): cv.positive_float,
                    vol.Optional("nov", default=1.5): cv.positive_float,
                    vol.Optional("dec", default=1.5): cv.positive_float
                })

SCHEMAS = [
    SENSOR_SCHEMA,
CHARGER_SCHEMA,
HOURS_SCHEMA,
PRICEAWARE_SCHEMA,
MONTHS_SCHEMA
]

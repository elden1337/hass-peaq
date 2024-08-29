import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME
from peaqevcore.common.spotprice.models.spotprice_type import SpotPriceType
from peaqevcore.services.locale.Locale import LOCALES

from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    CHARGERTYPES
from custom_components.peaqev.peaqservice.util.constants import (
    CAUTIONHOURTYPE_NAMES, INSTALLATIONTYPES, SPOTPRICE_VALUETYPES,
    CautionHourType)

TYPE_SCHEMA = vol.Schema(
    {
        vol.Optional(
            'peaqevtype',
            default='',
        ): vol.In(INSTALLATIONTYPES)
    }
)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional('powersensorincludescar', default=False): cv.boolean,
    }
)

CHARGER_SCHEMA = vol.Schema(
    {
        vol.Optional(
            'chargertype',
            default='',
        ): vol.In(CHARGERTYPES),
        vol.Optional(
            'locale',
            default='',
        ): vol.In(LOCALES),
    }
)

CHARGER_DETAILS_SCHEMA = vol.Schema(
    {
        vol.Optional('chargerid'): cv.string,
    }
)

OUTLET_DETAILS_SCHEMA = vol.Schema(
    {
        vol.Optional('outletswitch'): cv.string,
        vol.Optional('outletpowermeter'): cv.string,
    }
)

HOURS_SCHEMA = vol.Schema(
    {
        vol.Optional('nonhours'): cv.multi_select(list(range(0, 24))),
        vol.Optional('cautionhours'): cv.multi_select(list(range(0, 24))),
    }
)

PRICEAWARE_HOURS_SCHEMA = vol.Schema(
    {
        vol.Optional('priceaware_nonhours'): cv.multi_select(list(range(0, 24))),
    }
)

PRICEAWARE_SCHEMA = vol.Schema(
    {
        vol.Optional('priceaware', default=False): cv.boolean,
        vol.Optional(
                        'spotprice_type',
                        default=SpotPriceType.Auto.value,
                    ): vol.In(SPOTPRICE_VALUETYPES),
        vol.Optional('custom_price_sensor'): cv.string,
        vol.Optional('absolute_top_price'): cv.positive_float,
        vol.Optional('dynamic_top_price', default=False): cv.boolean,
        vol.Optional('min_priceaware_threshold_price'): cv.positive_float,
        vol.Optional(
            'cautionhour_type',
            default=CautionHourType.INTERMEDIATE.value,
        ): vol.In(CAUTIONHOURTYPE_NAMES),
    }
)

MONTHS_SCHEMA = vol.Schema(
    {
        vol.Optional('jan', default=1.5): cv.positive_float,
        vol.Optional('feb', default=1.5): cv.positive_float,
        vol.Optional('mar', default=1.5): cv.positive_float,
        vol.Optional('apr', default=1.5): cv.positive_float,
        vol.Optional('may', default=1.5): cv.positive_float,
        vol.Optional('jun', default=1.5): cv.positive_float,
        vol.Optional('jul', default=1.5): cv.positive_float,
        vol.Optional('aug', default=1.5): cv.positive_float,
        vol.Optional('sep', default=1.5): cv.positive_float,
        vol.Optional('oct', default=1.5): cv.positive_float,
        vol.Optional('nov', default=1.5): cv.positive_float,
        vol.Optional('dec', default=1.5): cv.positive_float,
        vol.Optional('use_peak_history', default=False): cv.boolean,
    }
)

SCHEMAS = [
    SENSOR_SCHEMA,
    CHARGER_SCHEMA,
    HOURS_SCHEMA,
    PRICEAWARE_SCHEMA,
    MONTHS_SCHEMA,
]

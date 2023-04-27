import asyncio
import logging

from homeassistant.core import HomeAssistant

from custom_components.peaqev.peaqservice.chargertypes.icharger_type import \
    IChargerType
from custom_components.peaqev.peaqservice.chargertypes.models.chargertypes_enum import \
    ChargerType
from custom_components.peaqev.peaqservice.chargertypes.types.chargeamps import \
    ChargeAmps
from custom_components.peaqev.peaqservice.chargertypes.types.easee import Easee
from custom_components.peaqev.peaqservice.chargertypes.types.garowallbox import \
    GaroWallBox
from custom_components.peaqev.peaqservice.chargertypes.types.no_charger import \
    NoCharger
from custom_components.peaqev.peaqservice.chargertypes.types.outlet import \
    SmartOutlet
from custom_components.peaqev.peaqservice.chargertypes.types.wallbox import \
    WallBox
from custom_components.peaqev.peaqservice.chargertypes.types.zaptec import \
    Zaptec
from custom_components.peaqev.peaqservice.hub.models.hub_options import \
    HubOptions

_LOGGER = logging.getLogger(__name__)


class ChargerTypeFactory:
    @staticmethod
    async def async_get_class(input_type: str):
        types_dict = {
            ChargerType.ChargeAmps: ChargeAmps,
            ChargerType.Easee: Easee,
            ChargerType.Outlet: SmartOutlet,
            ChargerType.GaroWallbox: GaroWallBox,
            ChargerType.Zaptec: Zaptec,
            ChargerType.WallBox: WallBox,
            ChargerType.NoCharger: NoCharger,
        }

        try:
            return types_dict.get(ChargerType(input_type))
        except Exception as e:
            _LOGGER.debug(f"Caught exception while parsing charger-type: {e}")
            raise ValueError

    @staticmethod
    async def async_create(hass: HomeAssistant, options: HubOptions) -> IChargerType:
        input_type = options.charger.chargertype
        try:
            charger = await ChargerTypeFactory.async_get_class(input_type)
            ret = charger(
                hass=hass, huboptions=options, chargertype=ChargerType(input_type)
            )

            _counter = 0
            while not ret.is_initialized and _counter < 10:
                _counter += 1
                ret.is_initialized = await ret.async_setup()
                if ret.is_initialized:
                    _LOGGER.info(
                        f"Set up charger-class for chargertype {input_type} is done. attempts:{_counter}"
                    )
                    return ret
                await asyncio.sleep(1)
            _LOGGER.exception(
                f"Did not manage to set up charge-class for {input_type} after {_counter} attempts. No entities found. The integration is probably not loaded."
            )
            raise Exception
        except Exception as e:
            _LOGGER.debug(
                f"Exception. Did not manage to set up charge-class for {input_type}: {e}"
            )
            raise Exception

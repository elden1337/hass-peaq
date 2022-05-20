import logging
from homeassistant.core import HomeAssistant
from ..const import DOMAIN  # pylint:disable=unused-import


async def _check_power_sensor(hass: HomeAssistant, powersensor: str) -> bool:
    ret = hass.states.get(powersensor).state
    try:
        float(ret)
        return True
    except Exception as e:
        msg = f"{powersensor} did not produce a valid state for {DOMAIN}. State was {ret}. Ex: {e}"
        _LOGGER.error(msg)
        return False

async def _validate_input_first(data: dict) -> dict[str, Any]:
    """ Validate the data can be used to set up a connection."""

    if len(data["name"]) < 3:
        raise ValueError
    if not data["name"].startswith("sensor."):
        data["name"] = f"sensor.{data['name']}"
    #if await _check_power_sensor(hass, data["name"]) is False:
    #    raise ValueError

    return {"title": data["name"]}

async def _validate_input_first_chargerid(data: dict) -> dict[str, Any]:
    """ Validate the chargerId"""
    #if len(data["chargerid"]) < 1:
    #    raise ValueError

    return {"title": data["name"]}
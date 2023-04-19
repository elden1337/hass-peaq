from datetime import datetime


def calculate_stop_len(nonhours) -> str:
    ret = ""
    for idx, h in enumerate(nonhours):
        if idx + 1 < len(nonhours):
            if _getuneven(nonhours[idx + 1], nonhours[idx]):
                ret = _get_stopped_string(h)
                break
        elif idx + 1 == len(nonhours):
            ret = _get_stopped_string(h)
            break
    return ret


def _get_stopped_string(h) -> str:
    val = h + 1 if h + 1 < 24 else h + 1 - 24
    if len(str(val)) == 1:
        return f"Charging stopped until 0{val}:00"
    return f"Charging stopped until {val}:00"


def _getuneven(first, second) -> bool:
    if second > first:
        return first - (second - 24) != 1
    return first - second != 1


async def async_currency_translation(
    value: float | str | None, currency, use_cent: bool = False
) -> str:
    value = "-" if value is None else round(float(value), 2)
    match currency:
        case "EUR":
            ret = f"{value}¢" if use_cent else f"€ {value}"
        case "SEK":
            ret = f"{value} öre" if use_cent else f"{value} kr"
        case "NOK":
            ret = f"{value} øre" if use_cent else f"{value} kr"
        case _:
            ret = f"{value} {currency}"
    return ret


async def async_set_avg_cost(avg_cost, currency, use_cent) -> str:
    standard = await async_currency_translation(
        value=avg_cost[0],
        currency=currency,
        use_cent=use_cent,
    )
    if avg_cost[1] is not None:
        if avg_cost[1] != avg_cost[0]:
            override = await async_currency_translation(
                value=avg_cost[1], currency=currency, use_cent=use_cent
            )
            return f"{override} ({standard})"
    return f"{standard}"


async def async_set_total_charge(max_charge) -> str:
    if max_charge[1] is not None:
        if max_charge[1] != max_charge[0]:
            return f"{max_charge[1]} kWh ({max_charge[0]} kWh)"
    return f"{max_charge[0]} kWh"


async def async_set_non_hours_display(non_hours: list, prices_tomorrow: list) -> list:
    ret = []
    for i in non_hours:
        if i < datetime.now().hour and len(prices_tomorrow) > 0:
            ret.append(f"{str(i)}⁺¹")
        elif i >= datetime.now().hour:
            ret.append(str(i))
    return ret


async def async_set_caution_hours_display(dynamic_caution_hours: dict) -> dict:
    ret = {}
    if len(dynamic_caution_hours) > 0:
        for h in dynamic_caution_hours:
            if h < datetime.now().hour:
                hh = f"{h}⁺¹"
            else:
                hh = h
            ret[hh] = f"{str((int(dynamic_caution_hours.get(h, 0) * 100)))}%"
    return ret


async def async_set_current_charge_permittance_display(
    non_hours, dynamic_caution_hours
) -> str:
    ret = 100
    hour = datetime.now().hour
    if hour in non_hours:
        ret = 0
    elif hour in dynamic_caution_hours.keys():
        ret = int(dynamic_caution_hours.get(hour) * 100)
    return f"{str(ret)}%"

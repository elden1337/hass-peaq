import logging
from datetime import datetime

from peaqevcore.services.hoursselection_service_new.models.hour_price import HourPrice

_LOGGER = logging.getLogger(__name__)


def calculate_stop_len(nonhours) -> str:
    ret = ""
    for idx, h in enumerate(nonhours):
        if idx + 1 < len(nonhours):
            if _get_uneven(nonhours[idx + 1], nonhours[idx]):
                ret = _get_stopped_string(h)
                break
        elif idx + 1 == len(nonhours):
            ret = _get_stopped_string(h)
            break
    return ret


def _get_stopped_string(
    h,
) -> str:  # todo: find out if stopped til further notice instead and type that.
    val = h + 1 if h + 1 < 24 else h + 1 - 24
    if val < 10:
        return f"Charging stopped until 0{val}:00"
    return f"Charging stopped until {val}:00"


def _get_uneven(first, second) -> bool:
    if second > first:
        return first - (second - 24) != 1
    return first - second != 1


def currency_translation(
    value: float | str | None, currency, use_cent: bool = False
) -> str:
    value = "-" if value is None else value
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


def set_avg_cost(avg_cost, currency, use_cent) -> str:
    standard = currency_translation(
        value=avg_cost[0],
        currency=currency,
        use_cent=use_cent,
    )
    if avg_cost[1] is not None:
        if avg_cost[1] != avg_cost[0]:
            override = currency_translation(
                value=avg_cost[1], currency=currency, use_cent=use_cent
            )
            return f"{override} ({standard})"
    return f"{standard}"


def set_total_charge(max_charge) -> str:
    if max_charge[1] is not None:
        if max_charge[1] != max_charge[0]:
            return f"{max_charge[1]} kWh ({max_charge[0]} kWh)"
    return f"{max_charge[0]} kWh"


def set_all_hours_display(future_hours: list[HourPrice]) -> dict:
    ret = {}
    for h in future_hours:
        dtstr = f"{h.dt.hour:02d}:{h.dt.minute:02d}"
        if h.dt.date() == datetime.now().date():
            dtstr = f"{dtstr}"
        else:
            dtstr = f"{dtstr}⁺¹"

        match h.permittance:
            case 0:
                ret[str(dtstr)] = "-"
            case 1:
                ret[str(dtstr)] = "Charge"
            case _:
                ret[str(dtstr)] = f"Caution {str(int(h.permittance * 100))}%"
    return ret


def set_non_hours_display(non_hours: list[datetime]) -> list:
    ret = []
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    for i in non_hours:
        if i.date() > now.date():
            ret.append(f"{str(i.hour)}⁺¹")
        elif i.date() == now.date():
            ret.append(str(i.hour))
    return ret


def set_caution_hours_display(dynamic_caution_hours: dict[datetime, float]) -> dict:
    ret = {}
    if len(dynamic_caution_hours) > 0:
        for h in dynamic_caution_hours:
            if h.date() > datetime.now().date():
                hh = f"{h.hour}⁺¹"
            else:
                hh = h.hour
            ret[hh] = f"{str((int(dynamic_caution_hours.get(h, 0) * 100)))}%"
    return ret


def set_current_charge_permittance_display(future_hours: list[HourPrice]) -> str:
    hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    ret = next(filter(lambda x: hour == x.dt, future_hours))
    return f"{str((ret.permittance or 0)*100)}%"

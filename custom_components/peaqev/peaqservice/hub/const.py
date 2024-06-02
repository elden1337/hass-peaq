from enum import Enum, auto

HOURLY = 'hourly'
TOTALPOWER = 'Total power'
HOUSEPOWER = 'House power'
CARPOWERSENSOR = 'CarPower-sensor'
CURRENTPEAKSENSOR = 'CurrentPeak-sensor'

AVERAGECONSUMPTION = 'Average consumption'
AVERAGECONSUMPTION_24H = 'Average consumption 24h'
CONSUMPTION_TOTAL_NAME = 'Energy including car'
CHARGERENABLED = 'Charger enabled'
CHARGER_DONE = 'Charger done'

PRICES_TOMORROW = 'prices_tomorrow'
NON_HOURS = 'non_hours'
DYNAMIC_CAUTION_HOURS = 'dynamic_caution_hours'
CURRENCY = 'currency'
AVERAGE_SPOTPRICE_DATA = 'average_spotprice_data'
AVERAGE_STDEV_DATA = 'average_stdev_data'
USE_CENT ='use_cent'
CURRENT_PEAK = 'current_peak'
AVERAGE_KWH_PRICE ='avg_kwh_price'
MAX_CHARGE ='max_charge'
MAX_PRICE ='max_price'
MIN_PRICE ='min_price'
FUTURE_HOURS = 'future_hours'
AVERAGE_MONTHLY ='average_monthly'
CHARGEROBJECT_VALUE = 'chargerobject_value'
HOUR_STATE = 'hour_state'
PRICES = 'prices'
CAUTION_HOURS = 'caution_hours'
AVERAGE_WEEKLY = 'average_weekly'
AVERAGE_30 = 'average_30'
OFFSETS ='offsets'
IS_PRICE_AWARE ='is_price_aware'
IS_SCHEDULER_ACTIVE ='is_scheduler_active'
CHARGECONTROLLER_STATUS ='chargecontroller_status'
SPOTPRICE_SOURCE = 'spotprice_source'

class LookupKeys(Enum):
    CHARGEROBJECT_VALUE = auto()
    CHARGER_DONE = auto()
    HOUR_STATE = auto()
    PRICES = auto()
    PRICES_TOMORROW = auto()
    NON_HOURS = auto()
    FUTURE_HOURS = auto()
    CAUTION_HOURS = auto()
    DYNAMIC_CAUTION_HOURS = auto()
    SPOTPRICE_SOURCE = auto()
    AVERAGE_SPOTPRICE_DATA = auto()
    AVERAGE_STDEV_DATA = auto()
    USE_CENT = auto()
    CURRENT_PEAK = auto()
    AVERAGE_KWH_PRICE = auto()
    MAX_CHARGE = auto()
    AVERAGE_WEEKLY = auto()
    AVERAGE_MONTHLY = auto()
    AVERAGE_30 = auto()
    CURRENCY = auto()
    OFFSETS = auto()
    IS_PRICE_AWARE = auto()
    IS_SCHEDULER_ACTIVE = auto()
    CHARGECONTROLLER_STATUS = auto()
    MAX_PRICE = auto()
    MIN_PRICE = auto()
    SCHEDULES = auto()

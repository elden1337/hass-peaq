from peaqevcore.common.enums.cautionhourtype import CautionHourType
from peaqevcore.common.spotprice.models.spotprice_type import SpotPriceType


"""NAMING CONSTANTS"""
CHARGERCONTROLLER = 'Charger controller'
HOURCONTROLLER = 'Hour controller'
PREDICTION = 'Prediction'
ALLOWEDCURRENT = 'Allowed current'
POWERCANARY = 'Power Canary'
SESSION = 'Session'
POWERCONTROLS = 'Power controls'
MONEYCONTROLS = 'Money sensors'
CONSUMPTION_INTEGRAL_NAME = 'Energy excluding car'
CONSUMPTION_TOTAL_NAME = 'Energy including car'
THRESHOLD = 'Threshold'
HUB = 'Hub'
SMARTOUTLET = 'SmartOutlet'

"""Chargertype helpers"""
PARAMS = 'params'
CHARGER = 'charger'
CHARGERID = 'chargerid'
CURRENT = 'current'
DOMAIN = 'domain'
NAME = 'name'

CAUTIONHOURTYPE_NAMES = [
    str(CautionHourType.SUAVE.value).capitalize(),
    str(CautionHourType.INTERMEDIATE.value).capitalize(),
    str(CautionHourType.AGGRESSIVE.value).capitalize(),
    str(CautionHourType.SCROOGE.value).capitalize(),
]

SPOTPRICE_VALUETYPES = [
    str(SpotPriceType.NordPool.value).capitalize(),
    str(SpotPriceType.EnergidataService.value).capitalize(),
    str(SpotPriceType.Auto.value).capitalize(),
]

TYPEREGULAR = 'Regular (requires power sensor)'
TYPELITE = 'Lite'

INSTALLATIONTYPES = [TYPEREGULAR, TYPELITE]

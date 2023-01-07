# from peaqevcore.models.hourselection.const import (
#     CAUTIONHOURTYPE as core_CAUTIONHOURTYPE
# )
from peaqevcore.models.hourselection.cautionhourtype import CautionHourType

"""CHARGERTYPES"""
CHARGERTYPE_CHARGEAMPS = "Chargeamps"
CHARGERTYPE_EASEE = "Easee"
CHARGERTYPE_GAROWALLBOX = "Garo Wallbox"
CHARGERTYPE_OUTLET = "Smart outdoor plug"
CHARGERTYPE_ZAPTEC = "Zaptec"

"""Lookup types for config flow"""
CHARGERTYPES = [
    CHARGERTYPE_CHARGEAMPS,
    CHARGERTYPE_EASEE,
    CHARGERTYPE_OUTLET,
    #CHARGERTYPE_GAROWALLBOX
    CHARGERTYPE_ZAPTEC
    ]

"""NAMING CONSTANTS"""
PEAQCONTROLLER = "Peaq controller"
CHARGERCONTROLLER = "Charger controller"
MONEY = "Money"
HOURCONTROLLER = "Hour controller"
PREDICTION = "Prediction"
TOTALPOWER = "Total power"
HOUSEPOWER = "House power"
ALLOWEDCURRENT = "Allowed current"
POWERCANARY = "Power Canary"
SESSION = "Session"
POWERCONTROLS = "Power controls"
CONSUMPTION_INTEGRAL_NAME = "Energy excluding car"
CONSUMPTION_TOTAL_NAME = "Energy including car"
THRESHOLD = "Threshold"
SQLSENSOR_BASENAME = "Monthly max peak"
SQLSENSOR_AVERAGEOFTHREE = "Average of three"
SQLSENSOR_AVERAGEOFTHREE_MIN = "Min of three"
SQLSENSOR_HIGHLOAD = "High load"
HUB = "Hub"
SMARTOUTLET = "SmartOutlet"

"""Chargertype helpers"""
PARAMS = "params"
CHARGER = "charger"
CHARGERID = "chargerid"
CURRENT = "current"
DOMAIN = "domain"
NAME = "name"

CAUTIONHOURTYPE_NAMES =[
    CautionHourType.SUAVE.value,
    CautionHourType.INTERMEDIATE.value,
    CautionHourType.AGGRESSIVE.value
]

TYPEREGULAR = "Regular (requires power sensor)"
TYPELITE = "Lite"

INSTALLATIONTYPES = [
    TYPEREGULAR,
    TYPELITE
]

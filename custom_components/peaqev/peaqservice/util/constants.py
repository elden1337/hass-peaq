from peaqevcore.models.const import (
    CAUTIONHOURTYPE_SUAVE,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_AGGRESSIVE,
    CAUTIONHOURTYPE as core_CAUTIONHOURTYPE
)
from peaqevcore.services.locale.querytypes.const import HOURLY as core_HOURLY, QUARTER_HOURLY as core_QUARTER_HOURLY

HOURLY = core_HOURLY
QUARTER_HOURLY = core_QUARTER_HOURLY

# CURRENTS_ONEPHASE_1_16 = {
#     3600: 16,
#     3150: 14,
#     2700: 12,
#     2250: 10,
#     1800: 8,
#     1350: 6
# } #moved to core
# CURRENTS_THREEPHASE_1_16 = {
#     11000: 16,
#     9625: 14,
#     8250: 12,
#     6875: 10,
#     5500: 8,
#     4100: 6
# } #moved to core
# CURRENTS_ONEPHASE_1_32 = {
#     7200: 32,
#     6750: 30,
#     6300: 28,
#     5850: 26,
#     5400: 24,
#     4950: 22,
#     4500: 20,
#     4050: 18,
#     3600: 16,
#     3150: 14,
#     2700: 12,
#     2250: 10,
#     1800: 8,
#     1350: 6
# } #moved to core
# CURRENTS_THREEPHASE_1_32 = {
#     22000: 32,
#     20625: 30,
#     19250: 28,
#     17875: 26,
#     16500: 24,
#     15125: 22,
#     13750: 20,
#     12375: 18,
#     11000: 16,
#     9625: 14,
#     8250: 12,
#     6875: 10,
#     5500: 8,
#     4100: 6
# } #moved to core


"""CHARGERTYPES"""
CHARGERTYPE_CHARGEAMPS = "Chargeamps"
CHARGERTYPE_EASEE = "Easee"
CHARGERTYPE_GAROWALLBOX = "Garo Wallbox"

"""Lookup types for config flow"""
CHARGERTYPES = [
    CHARGERTYPE_CHARGEAMPS,
    CHARGERTYPE_EASEE
    #CHARGERTYPE_GAROWALLBOX
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
CONSUMPTION_INTEGRAL_NAME = "Energy excluding car"
CONSUMPTION_TOTAL_NAME = "Energy including car"
CHARGERENABLED = "Charger enabled"
CHARGERDONE = "Charger done"
AVERAGECONSUMPTION = "Average consumption"
AVERAGECONSUMPTION_24H = "Average consumption 24h"
THRESHOLD = "Threshold"
SQLSENSOR_BASENAME = "Monthly max peak"
SQLSENSOR_AVERAGEOFTHREE = "Average of three"
SQLSENSOR_AVERAGEOFTHREE_MIN = "Min of three"
SQLSENSOR_HIGHLOAD = "High load"

"""Sql sensor helpers"""
SQLSENSOR_STATISTICS_TABLE = "statistics"
SQLSENSOR_STATISTICS_META_TABLE = "statistics_meta"

"""Chargertype helpers"""
UPDATECURRENT = "updatecurrent"
PARAMS = "params"
CHARGER = "charger"
CHARGERID = "chargerid"
CURRENT = "current"
DOMAIN = "domain"
NAME = "name"
ON = "on"
OFF = "off"
RESUME = "resume"
PAUSE = "pause"

"""States for the Hours-object"""
# moved to core
NON_HOUR = "Charging stopped"
CAUTION_HOUR = "Charging-permittance degraded"
CHARGING_PERMITTED = "Charging permitted"
# moved to core

CAUTIONHOURTYPE_NAMES =[
    CAUTIONHOURTYPE_SUAVE,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_AGGRESSIVE
]

CAUTIONHOURTYPE_DICT = core_CAUTIONHOURTYPE

TYPEREGULAR = "Regular (requires power sensor)"
TYPELITE = "Lite"

INSTALLATIONTYPES = [
    TYPEREGULAR,
    TYPELITE
]

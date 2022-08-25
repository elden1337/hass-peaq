from peaqevcore.models.hourselection.const import (
    CAUTIONHOURTYPE_SUAVE,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_AGGRESSIVE,
    CAUTIONHOURTYPE as core_CAUTIONHOURTYPE
)

#HOURLY = core_HOURLY
#QUARTER_HOURLY = core_QUARTER_HOURLY

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
#CHARGERENABLED = "Charger enabled" #core
#CHARGERDONE = "Charger done" #core
#AVERAGECONSUMPTION = "Average consumption" # core
#AVERAGECONSUMPTION_24H = "Average consumption 24h" # core
THRESHOLD = "Threshold"
SQLSENSOR_BASENAME = "Monthly max peak"
SQLSENSOR_AVERAGEOFTHREE = "Average of three"
SQLSENSOR_AVERAGEOFTHREE_MIN = "Min of three"
SQLSENSOR_HIGHLOAD = "High load"

"""Sql sensor helpers"""
#SQLSENSOR_STATISTICS_TABLE = "statistics"
#SQLSENSOR_STATISTICS_META_TABLE = "statistics_meta"

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
#NON_HOUR = "Charging stopped"  # core
#CAUTION_HOUR = "Charging-permittance degraded" # core
#CHARGING_PERMITTED = "Charging permitted" # core
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

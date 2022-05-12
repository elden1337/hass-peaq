from peaqevcore.Models import (
    CAUTIONHOURTYPE_SUAVE,
    CAUTIONHOURTYPE_INTERMEDIATE,
    CAUTIONHOURTYPE_AGGRESSIVE,
    CAUTIONHOURTYPE as core_CAUTIONHOURTYPE
)

CURRENTS_ONEPHASE_1_16 = {3600: 16, 3150: 14, 2700: 12, 2250: 10, 1800: 8, 1350: 6} #moved to core
CURRENTS_THREEPHASE_1_16 = {11000: 16, 9625: 14, 8250: 12, 6875: 10, 5500: 8, 4100: 6} #moved to core
CURRENTS_ONEPHASE_1_32 = {7200: 32, 6750: 30, 6300: 28, 5850: 26, 5400: 24, 4950: 22, 4500: 20, 4050: 18, 3600: 16, 3150: 14, 2700: 12, 2250: 10, 1800: 8, 1350: 6} #moved to core
CURRENTS_THREEPHASE_1_32 = {22000: 32, 20625: 30, 19250: 28, 17875: 26, 16500: 24, 15125: 22, 13750: 20, 12375: 18, 11000: 16, 9625: 14, 8250: 12, 6875: 10, 5500: 8, 4100: 6} #moved to core

CHARGERTYPE_CHARGEAMPS = "Chargeamps"
CHARGERTYPE_EASEE = "Easee"

LOCALE_SE_GOTHENBURG = "Gothenburg, Sweden"
LOCALE_SE_KARLSTAD = "Karlstad, Sweden"
LOCALE_SE_KRISTINEHAMN = "Kristinehamn, Sweden"
LOCALE_SE_NACKA_NORMAL = "Nacka, Sweden (Normal tariffe)"
#LOCALE_SE_NACKA_TIMEDIFF = "Nacka, Sweden (Time differentiated tariffe)"
LOCALE_SE_PARTILLE = "Partille, Sweden"
LOCALE_DEFAULT = "Other, just want to test"
LOCALE_SE_SALA = "Sala-Heby Energi AB, Sweden"
LOCALE_SE_MALUNG_SALEN = "Malung-Sälen, Sweden (Malungs elverk)"
LOCALE_SE_SKOVDE = "Skövde, Sweden"
LOCALE_SE_SOLLENTUNA = "Sollentuna Energi, Sweden"

"""Lookup types for config flow"""
CHARGERTYPES = [
    CHARGERTYPE_CHARGEAMPS,
    CHARGERTYPE_EASEE
    ]

"""Lookup locales for config flow"""
LOCALES = [
    LOCALE_SE_GOTHENBURG,
    LOCALE_SE_KARLSTAD,
    LOCALE_SE_KRISTINEHAMN,
    LOCALE_SE_MALUNG_SALEN,
    LOCALE_SE_NACKA_NORMAL,
    LOCALE_SE_PARTILLE,
    LOCALE_SE_SALA,
    LOCALE_SE_SKOVDE,
    LOCALE_SE_SOLLENTUNA,
    LOCALE_DEFAULT
    ]

"""Naming constants"""
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
HOURLY = "hourly"
THRESHOLD = "Threshold"
SQLSENSOR_BASENAME = "Monthly max peak"
SQLSENSOR_AVERAGEOFTHREE = "Average of three"
SQLSENSOR_AVERAGEOFTHREE_MIN = "Min of three"
SQLSENSOR_HIGHLOAD = "High load"

"""Peak querytypes"""
QUERYTYPE_BASICMAX = "BasicMax"
QUERYTYPE_AVERAGEOFTHREEDAYS = "AverageOfThreeDays"
QUERYTYPE_AVERAGEOFTHREEHOURS = "AverageOfThreeHours"
QUERYTYPE_AVERAGEOFTHREEDAYS_MIN = "AverageOfThreeDays_Min"
QUERYTYPE_AVERAGEOFTHREEHOURS_MIN = "AverageOfThreeHours_Min"
QUERYTYPE_AVERAGEOFFIVEDAYS = "AverageOfFiveDays"
QUERYTYPE_AVERAGEOFFIVEDAYS_MIN = "AverageOfFiveDays_Min"
QUERYTYPE_HIGHLOAD = "HighLoad"

QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19 = "sala"
QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN = "sala"

QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22 = "skövde"
QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR = "kristinehamn"

QUERYTYPE_SOLLENTUNA = "sollentuna"
QUERYTYPE_SOLLENTUNA_MIN = "sollentuna_min"

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
NON_HOUR = "Charging stopped"
CAUTION_HOUR = "Charging-permittance degraded"
CHARGING_PERMITTED = "Charging permitted"

"""Cautionhour types"""
#CAUTIONHOURNAME_SUAVE = "Suave"
#CAUTIONHOURNAME_INTERMEDIATE = "Intermediate"
#CAUTIONHOURNAME_AGGRESSIVE = "Aggressive"

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

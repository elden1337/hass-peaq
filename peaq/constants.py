from enum import Enum

CHARGECONTROLLER = Enum("chargestate", "Idle Start Stop Done Error")
CURRENTS = {3600: 16,3200: 14,2700: 12,	2300: 10,1800: 8,1300: 6}
CURRENTS_3_PHASE = {11000: 16,9600: 14,8200: 12,6900: 10,5500: 8,4100: 6}

CHARGERTYPE_CHARGEAMPS = "Chargeamps"
CHARGERTYPE_EASEE = "Easee"

LOCALE_SE_GOTHENBURG = "Gothenburg, Sweden"
LOCALE_SE_KARLSTAD = "Karlstad, Sweden"
LOCALE_SE_KRISTINEHAMN = "Kristinehamn, Sweden"
LOCALE_SE_NACKA = "Nacka, Sweden"
LOCALE_SE_PARTILLE = "Partille, Sweden"

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
    LOCALE_SE_NACKA,
    LOCALE_SE_PARTILLE
    ]

"""Naming constants"""
PEAQCONTROLLER = "Peaq controller"
TOTALPOWER = "Total Power"
CONSUMPTION_INTEGRAL_NAME = "Energy excluding car"
CONSUMPTION_TOTAL_NAME = "Energy including car" 

"""Peak querytypes"""
QUERYTYPE_BASICMAX = "BasicMax"
QUERYTYPE_AVERAGEOFTHREEDAYS = "AverageOfThreeDays"
QUERYTYPE_AVERAGEOFTHREEDAYS_MIN = "AverageOfThreeDays_Min"
QUERYTYPE_HIGHLOAD = "HighLoad"

"""Sql sensor helpers"""
SQLSENSOR.STATISTICS_TABLE = "statistics"
SQLSENSOR.STATISTICS_META_TABLE= "statistics_meta"
SQLSENSOR.BASENAME = "Monthly max peak"
from custom_components.peaqev.peaqservice.util.constants import (
    SQLSENSOR_BASENAME,
    SQLSENSOR_AVERAGEOFTHREE,
    SQLSENSOR_AVERAGEOFTHREE_MIN,
    SQLSENSOR_HIGHLOAD,
    QUERYTYPE_BASICMAX,
    QUERYTYPE_AVERAGEOFTHREEDAYS,
    QUERYTYPE_AVERAGEOFTHREEDAYS_MIN,
    QUERYTYPE_AVERAGEOFTHREEHOURS,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MIN,
    QUERYTYPE_HIGHLOAD,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN,
    QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22,
    QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR,
    SQLSENSOR_STATISTICS_TABLE,
    SQLSENSOR_STATISTICS_META_TABLE
    )
import custom_components.peaqev.peaqservice.util.extensionmethods as ex

class SQLSensorHelper():
    def __init__(self, sensor :str):
        self._sensor = ex.nametoid(sensor)

        PREFIX_MAX = f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        SUFFIX_MAX = f' GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1'

        PREFIX_MIN = f''
        SUFFIX_MIN = f''

        PREFIX_AVG = f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        SUFFIX_AVG_PER_HOUR = f' GROUP BY strftime(\'%H\', start) ORDER BY MAX(state) DESC LIMIT 3)'
        SUFFIX_AVG_PER_DAY = f' GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)'

        self.basequeries = {
            "max": [PREFIX_MAX, SUFFIX_MAX],
            "min": [PREFIX_MIN, SUFFIX_MIN],
            "avg_hour": [PREFIX_AVG, SUFFIX_AVG_PER_HOUR],
            "avg_day": [PREFIX_AVG, SUFFIX_AVG_PER_DAY]
        }

    def getquerytype(self, type):
        QUERYTYPES = {
            QUERYTYPE_BASICMAX: {
                'query': f'{self.basequeries["max"][0]}{self.basequeries["max"][1]}',
                'name': f'{SQLSENSOR_BASENAME}',
                'comment': 'Partille, SE etc'
            },
            QUERYTYPE_AVERAGEOFTHREEDAYS: {
                'query': f'{self.basequeries["avg_day"][0]}{self.basequeries["avg_day"][1]}',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': 'Gothenburg, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS: {
                'query': f'{self.basequeries["avg_hour"][0]}{self.basequeries["avg_hour"][1]}',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': ''
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MIN: {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%H\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': ''
            },
            QUERYTYPE_AVERAGEOFTHREEDAYS_MIN: {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Gothenburg, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19: {
                'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 7 AND 19 GROUP BY strftime(\'%H\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19}',
                'comment': 'Sala, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN: {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 7 AND 19 GROUP BY strftime(\'%H\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN}',
                'comment': 'Sala, SE'
            },
            QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR: {
                'query': f'{self.basequeries["max"][0]} AND (({Datepart.add("lteq","weekday",4)} AND {Datepart.add("in","hour",7,8,9,10,11,12,13,14,15,16)} AND {Datepart.add("in","month",12,1,2,3)}) OR ({Datepart.add("in", "month",4,5,6,7,8,9,10,11)}) ){self.basequeries["max"][1]}',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR}',
                'comment': 'Kristinehamn, SE'
            },
            QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22: {
                'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 6 AND 22 AND cast(strftime(\'%m\', start) as int) in (11,12,1,2,3) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22}',
                'comment': 'Skövde, SE'
            },
            QUERYTYPE_HIGHLOAD: {
                'query': f'SELECT IFNULL(MAX(state),0) as state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 8 AND 18 GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_HIGHLOAD}',
                'comment': '(karlstad). Only used Nov - Mar, weekdays between 08-18'
            }
        }

        return QUERYTYPES[type]


class Datepart:
    DIVIDENTS = {
        "eq": "= ",
        "lt": "< ",
        "gt": "> ",
        "not": "<> ",
        "lteq": "<= ",
        "gteq": ">= ",
        "in": "IN "
    }

    DATETIMEPARTS = {
        "weekday": "w",
        "month": "m",
        "hour": "H"
    }

    @staticmethod
    def add(divident: str, dtpart: str, *args: int) -> str:
        _base = Datepart._strftime_base(Datepart.DATETIMEPARTS[dtpart])
        _arg = str(args) if len(args) > 1 else str(args[0])
        _divident = Datepart.DIVIDENTS[divident]
        return _base + _divident + _arg

    @staticmethod
    def _strftime_base(type: str) -> str:
        return f"cast(strftime(\'%{type}\', start) as int) "



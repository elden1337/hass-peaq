import custom_components.peaqev.peaqservice.util.extensionmethods as ex
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
    QUERYTYPE_AVERAGEOFFIVEDAYS,
    QUERYTYPE_AVERAGEOFFIVEDAYS_MIN,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19,
    QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN,
    QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22,
    QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR,
    SQLSENSOR_STATISTICS_TABLE,
    SQLSENSOR_STATISTICS_META_TABLE, QUERYTYPE_SOLLENTUNA, QUERYTYPE_SOLLENTUNA_MIN
)


class SQLSensorHelper():
    def __init__(self, sensor: str):
        self._sensor = ex.nametoid(sensor)

        PREFIX_MAX = f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        SUFFIX_MAX = ' GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1'
        PREFIX_AVG_MIN = f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        PREFIX_AVG = f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        SUFFIX_AVG_HOUR = ' GROUP BY strftime(\'%H\', start) ORDER BY MAX(state) DESC LIMIT 3)'
        SUFFIX_AVG_DAY = ' GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)'
        PREFIX_AVG_5 = f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        PREFIX_AVG_5_MIN = f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date())'
        SUFFIX_AVG_5_DAY = ' GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 5)'

        self.basequeries = {
            "max": [PREFIX_MAX, SUFFIX_MAX],
            "min_hour": [PREFIX_AVG_MIN, SUFFIX_AVG_HOUR],
            "min_day": [PREFIX_AVG_MIN, SUFFIX_AVG_DAY],
            "avg_hour": [PREFIX_AVG, SUFFIX_AVG_HOUR],
            "avg_day": [PREFIX_AVG, SUFFIX_AVG_DAY],
            "min_day_5": [PREFIX_AVG_5_MIN, SUFFIX_AVG_5_DAY],
            "avg_day_5": [PREFIX_AVG_5, SUFFIX_AVG_5_DAY]
        }

    def getquerytype(self, query_type):
        QUERYTYPES = {
            QUERYTYPE_BASICMAX: {
                'query': sql.query(
                    self.basequeries["max"][0],
                    self.basequeries["max"][1]
                ),
                'name': f'{SQLSENSOR_BASENAME}',
                'comment': 'Partille, SE etc'
            },
            QUERYTYPE_AVERAGEOFTHREEDAYS: {
                'query': sql.query(
                    self.basequeries["avg_day"][0],
                    self.basequeries["avg_day"][1]
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': 'Gothenburg, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS: {
                'query': sql.query(
                    self.basequeries["avg_hour"][0],
                    self.basequeries["avg_hour"][1]
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': ''
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MIN: {
                'query': sql.query(
                    self.basequeries["min_hour"][0],
                    self.basequeries["min_hour"][1]
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': ''
            },
            QUERYTYPE_AVERAGEOFTHREEDAYS_MIN: {
                'query': sql.query(
                    self.basequeries["min_day"][0],
                    self.basequeries["min_day"][1]
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Gothenburg, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19: {
                'query': sql.query(
                    self.basequeries["avg_hour"][0],
                    self.basequeries["avg_hour"][0],
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4),
                    sql.AND,
                    sql.datepart("in", "hour", 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19}',
                'comment': 'Sala, SE'
            },
            QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN: {
                'query': sql.query(
                    self.basequeries["min_hour"][0],
                    self.basequeries["min_hour"][0],
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4),
                    sql.AND,
                    sql.datepart("in", "hour", 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN}',
                'comment': 'Sala, SE'
            },
            QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR: {
                'query': sql.query(
                    self.basequeries["max"][0],
                    self.basequeries["max"][1],
                    sql.group(
                        sql.group(
                            sql.AND,
                            sql.datepart("lteq", "weekday", 4),
                            sql.AND,
                            sql.datepart("in", "hour", 7, 8, 9, 10, 11, 12, 13, 14, 15, 16),
                            sql.AND,
                            sql.datepart("in", "month", 12, 1, 2, 3)
                        ),
                        sql.OR,
                        sql.datepart("in", "month", 4, 5, 6, 7, 8, 9, 10, 11)
                    )
                ),
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR}',
                'comment': 'Kristinehamn, SE'
            },
            QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22: {
                'query': sql.query(
                    self.basequeries["max"][0],
                    self.basequeries["max"][1],
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4),
                    sql.AND,
                    sql.datepart("gteq", "hour", 6),
                    sql.AND,
                    sql.datepart("lteq", "hour", 22),
                    sql.AND,
                    sql.datepart("in", "month", 11, 12, 1, 2, 3)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22}',
                'comment': 'Skövde, SE'
            },
            QUERYTYPE_HIGHLOAD: {
                'query': sql.query(
                    self.basequeries["max"][0],
                    self.basequeries["max"][1],
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4),
                    sql.AND,
                    sql.datepart("gteq", "hour", 8),
                    sql.AND,
                    sql.datepart("lteq", "hour", 18)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_HIGHLOAD}',
                'comment': '(karlstad). Only used Nov - Mar, weekdays between 08-18'
            },
            QUERYTYPE_AVERAGEOFFIVEDAYS: {
                'query': sql.query(
                    self.basequeries["avg_day_5"][0],
                    self.basequeries["avg_day_5"][1],
                    sql.AND,
                    sql.datepart("gteq", "hour", 7),
                    sql.AND,
                    sql.datepart("lteq", "hour", 18)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Malung-Sälen, SE'
            },
            QUERYTYPE_AVERAGEOFFIVEDAYS_MIN: {
                'query': sql.query(
                    self.basequeries["min_day_5"][0],
                    self.basequeries["min_day_5"][1],
                    sql.AND,
                    sql.datepart("gteq", "hour", 7),
                    sql.AND,
                    sql.datepart("lteq", "hour", 18)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Malung-Sälen, SE'
            },
            QUERYTYPE_SOLLENTUNA: {
                'query': sql.query(
                    self.basequeries["avg_hour"][0],
                    self.basequeries["avg_hour"][1],
                    sql.AND,
                    sql.datepart("gteq", "hour", 7),
                    sql.AND,
                    sql.datepart("lteq", "hour", 18),
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': 'Sollentuna, SE'
            },
            QUERYTYPE_SOLLENTUNA_MIN: {
                'query': sql.query(
                    self.basequeries["min_hour"][0],
                    self.basequeries["min_hour"][1],
                    sql.AND,
                    sql.datepart("gteq", "hour", 7),
                    sql.AND,
                    sql.datepart("lteq", "hour", 18),
                    sql.AND,
                    sql.datepart("lteq", "weekday", 4)
                ),
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Sollentuna, SE'
            },
        }

        return QUERYTYPES[query_type]


class sql:
    @staticmethod
    def query(prefix: str, suffix: str, *params: str):
        paramret = ""
        for p in params:
            paramret = paramret+p
        return prefix+paramret+suffix

    @staticmethod
    def group(*contents: str) -> str:
        ret = ""
        for c in contents:
            ret += c
        return f"({ret})"

    AND = " AND "
    OR = " OR "
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
    def datepart(divident: str, dtpart: str, *args: int) -> str:
        _base = sql._strftime_base(sql.DATETIMEPARTS[dtpart])
        _arg = str(args) if len(args) > 1 else str(args[0])
        _divident = sql.DIVIDENTS[divident]
        return _base + _divident + _arg

    @staticmethod
    def _strftime_base(time_type: str) -> str:
        return f"cast(strftime(\'%{time_type}\', start) as int) "


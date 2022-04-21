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

    def getquerytype(self, type):
        QUERYTYPES = {
            f"{QUERYTYPE_BASICMAX}": {
                'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}',
                'comment': 'Partille, SE etc'
            },
            f"{QUERYTYPE_AVERAGEOFTHREEDAYS}": {
                'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': 'Gothenburg, SE'
            },
            f"{QUERYTYPE_AVERAGEOFTHREEHOURS}": {
                'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE}',
                'comment': ''
            },
            f"{QUERYTYPE_AVERAGEOFTHREEHOURS_MIN}": {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': ''
            },
            f"{QUERYTYPE_AVERAGEOFTHREEDAYS_MIN}": {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_AVERAGEOFTHREE_MIN}',
                'comment': 'Gothenburg, SE'
            },
            f"{QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19}": {
                'query': f'SELECT IFNULL(ROUND(AVG(daymax),2),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 7 AND 19 GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19}',
                'comment': 'Sala, SE'
            },
            f"{QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN}": {
                'query': f'SELECT IFNULL(min(daymax),0) as state FROM ( SELECT MAX(state) as daymax FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 7 AND 19 GROUP BY strftime(\'%h\', start) ORDER BY MAX(state) DESC LIMIT 3)',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_AVERAGEOFTHREEHOURS_MON_FRI_07_19_MIN}',
                'comment': 'Sala, SE'
            },
            f"{QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR}": {
                'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND ((cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 7 AND 17 AND cast(strftime(\'%m\', start) as int) in (12,1,2,3)) OR (cast(strftime(\'%m\', start) as int) between 4 and 12) ) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_BASICMAX_MON_FRI_07_17_DEC_MAR_ELSE_REGULAR}',
                'comment': 'Kristinehamn, SE'
            },
            f"{QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22}": {
                'query': f'SELECT IFNULL(MAX(state),0) AS state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id = "{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 6 AND 22 AND cast(strftime(\'%m\', start) as int) in (11,12,1,2,3) GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}, {QUERYTYPE_MAX_NOV_MAR_MON_FRI_06_22}',
                'comment': 'Skövde, SE'
            },
            f"{QUERYTYPE_HIGHLOAD}": {
                'query': f'SELECT IFNULL(MAX(state),0) as state FROM "{SQLSENSOR_STATISTICS_TABLE}" WHERE metadata_id = (SELECT id FROM "{SQLSENSOR_STATISTICS_META_TABLE}" WHERE statistic_id ="{self._sensor}" LIMIT 1) AND strftime(\'%Y\', start) = strftime(\'%Y\', date()) AND strftime(\'%m\', start) = strftime(\'%m\', date()) AND cast(strftime(\'%w\', start) as int) <= 4 AND cast(strftime(\'%H\', start) as int) between 8 AND 18 GROUP BY strftime(\'%d\', start) ORDER BY MAX(state) DESC LIMIT 1',
                'name': f'{SQLSENSOR_BASENAME}, {SQLSENSOR_HIGHLOAD}',
                'comment': '(karlstad). Only used Nov - Mar, weekdays between 08-18'
            }
        }

        return QUERYTYPES[type]
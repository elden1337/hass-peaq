from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
from custom_components.peaqev.sensors.integration_sensor import PeaqIntegrationSensor
from custom_components.peaqev.sensors.sql_sensor import PeaqSQLSensor
from custom_components.peaqev.peaqservice.util.sqlsensorhelper import SQLSensorHelper
from custom_components.peaqev.sensors.power_sensor import (PeaqPowerSensor, PeaqAmpSensor, PeaqHousePowerSensor)
from custom_components.peaqev.sensors.prediction_sensor import PeaqPredictionSensor
from custom_components.peaqev.sensors.threshold_sensor import PeaqThresholdSensor
from custom_components.peaqev.sensors.peaq_sensor import PeaqSensor
import custom_components.peaqev.peaqservice.util.extensionmethods as ex
from custom_components.peaqev.peaqservice.util.constants import (
    CONSUMPTION_TOTAL_NAME,
    CONSUMPTION_INTEGRAL_NAME
    )

from custom_components.peaqev.const import (
    DOMAIN)

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from homeassistant.components.recorder import DEFAULT_DB_FILE, DEFAULT_URL
import logging

_LOGGER = logging.getLogger(__name__)

async def gather_sql_sensors(hass, hub, entry_id):
    peaqsqlsensors = []
    peaks = hub.locale.data

    db_url = DEFAULT_URL.format(hass_config_path=hass.config.path(DEFAULT_DB_FILE))
    engine = sqlalchemy.create_engine(db_url)
    sessmaker = scoped_session(sessionmaker(bind=engine))
    sqlsensor = hub.totalhourlyenergy.entity
    sql = SQLSensorHelper(sqlsensor).getquerytype(peaks.charged_peak)
    peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql, entry_id))

    if peaks.charged_peak != peaks.observed_peak:
        _LOGGER.warn("i want to create a second sensor")
        sql2 = SQLSensorHelper(sqlsensor).getquerytype(peaks.observed_peak)
        peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql2, entry_id))
    return peaqsqlsensors

async def gather_Sensors(hub, entry_id) -> list:
    peaqsensors = []
    if hub._powersensor_includes_car is True:
        peaqsensors.append(PeaqHousePowerSensor(hub, entry_id))
    else:
        peaqsensors.append(PeaqPowerSensor(hub, entry_id))
    peaqsensors.append(PeaqAmpSensor(hub, entry_id))
    peaqsensors.append(PeaqAverageSensor(hub, entry_id))
    peaqsensors.append(PeaqPredictionSensor(hub, entry_id))
    peaqsensors.append(PeaqThresholdSensor(hub, entry_id))
    peaqsensors.append(PeaqSensor(hub, entry_id))
    return peaqsensors

async def gather_integration_sensors(hub, entry_id):
    peaqintegrationsensors = []

    if hub._powersensor_includes_car is True:
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.house.id}",
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                entry_id
            )
        )
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.total.entity,
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id
            )
        )
    else:
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.house.entity,
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}",
                entry_id
            )
        )
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.total.id}",
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}",
                entry_id
            )
        )
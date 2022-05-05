"""Platform for sensor integration."""
import logging
from custom_components.peaqev.sensors.utility_sensor import (
    PeaqUtilitySensor,
    METER_OFFSET,
    PERIODS
)

from custom_components.peaqev.sensors.integration_sensor import PeaqIntegrationSensor
from custom_components.peaqev.sensors.average_sensor import PeaqAverageSensor
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

from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from homeassistant.components.recorder import DEFAULT_DB_FILE, DEFAULT_URL

from .const import (
    DOMAIN)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_entry(hass : HomeAssistant, config: ConfigEntry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    
    hub = hass.data[DOMAIN]["hub"]

    peaqsensors = await gather_Sensors(hass, hub)
    async_add_entities(peaqsensors, update_before_add = True)

    peaqintegrationsensors = []
    if hub._powersensor_includes_car is True:
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.house.id}",
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}"
            )
        )
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.total.entity,
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}"
            )
        )
    else:
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                hub.power.house.entity,
                f"{ex.nametoid(CONSUMPTION_INTEGRAL_NAME)}"
            )
        )
        peaqintegrationsensors.append(
            PeaqIntegrationSensor(
                hub,
                f"sensor.{DOMAIN}_{hub.power.total.id}",
                f"{ex.nametoid(CONSUMPTION_TOTAL_NAME)}"
            )
        )
    async_add_entities(peaqintegrationsensors, update_before_add=True)

    integrationsensors = [ex.nametoid(CONSUMPTION_TOTAL_NAME), ex.nametoid(CONSUMPTION_INTEGRAL_NAME)]
    peaqutilitysensors = []

    for i in integrationsensors:
        for p in PERIODS:
            peaqutilitysensors.append(PeaqUtilitySensor(hub, i, p, METER_OFFSET))
    
    async_add_entities(peaqutilitysensors, update_before_add = True)

    #sql sensors
    peaqsqlsensors = []
    peaks = hub.locale

    db_url = DEFAULT_URL.format(hass_config_path=hass.config.path(DEFAULT_DB_FILE))
    engine = sqlalchemy.create_engine(db_url)
    sessmaker = scoped_session(sessionmaker(bind=engine))
    sqlsensor = hub.totalhourlyenergy.entity
    sql = SQLSensorHelper(sqlsensor).getquerytype(peaks.data.charged_peak)
    peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql, config.entry_id))

    if peaks.data.charged_peak != peaks.data.observed_peak:
        sql2 = SQLSensorHelper(sqlsensor).getquerytype(peaks.data.observed_peak)
        peaqsqlsensors.append(PeaqSQLSensor(hub, sessmaker, sql2, config.entry_id))
    #sql sensors
    
    async_add_entities(peaqsqlsensors, update_before_add = True)

async def gather_Sensors(hass: HomeAssistant, hub) -> list:
    peaqsensors = []
    if hub._powersensor_includes_car is True:
        peaqsensors.append(PeaqHousePowerSensor(hub, hass))
    else:
        peaqsensors.append(PeaqPowerSensor(hub, hass))
    peaqsensors.append(PeaqAmpSensor(hub, hass))
    peaqsensors.append(PeaqAverageSensor(hub))
    peaqsensors.append(PeaqPredictionSensor(hub))
    peaqsensors.append(PeaqThresholdSensor(hub))
    peaqsensors.append(PeaqSensor(hub))
    return peaqsensors

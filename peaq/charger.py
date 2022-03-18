
import logging
import custom_components.peaq.peaq.constants
from custom_components.peaq.peaq.chargecontroller import ChargeController
from custom_components.peaq.peaq.prediction import Prediction
from custom_components.peaq.peaq.threshold import Threshold
from homeassistant.helpers.event import async_track_state_change
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    HassJob,
    HomeAssistant,
    State,
    callback,
)

_LOGGER = logging.getLogger(__name__)


class Charger:
    def __init__(self):
        pass

    def Charge():
        #   trigger:
#   - platform: state
#     entity_id: sensor.hake_2012019145m_1
#     from: Available
#     to: Connected
#   condition:
#   - condition: state
#     entity_id: alarm_control_panel.sector_alarmpanel_02849911
#     state: disarmed
#   action:
#   - service: input_boolean.turn_off
#     target:
#       entity_id: input_boolean.chargeamps_charging_done
#   - service: chargeamps.set_light
#     data:
#       dimmer: high
#   - repeat:
#       while:
#       - condition: template
#         value_template: '{{is_state(''input_boolean.chargeamps_charging_done'', ''off'')
#           and (states(''sensor.hake_2012019145m_1'') != "Available")}}

#           '
#       sequence:
#       - wait_template: '{{is_state(''sensor.chargeamps_let_charge'', ''Start'')}}

#           '
#       - service: chargeamps.enable
#       - delay:
#           hours: 0
#           minutes: 2
#           seconds: 0
#           milliseconds: 0
#       - wait_template: '{{is_state(''sensor.chargeamps_let_charge'', ''Stop'') or
#           is_state(''sensor.chargeamps_let_charge'', ''Done'')}}

#           '
#       - choose:
#         - conditions:
#           - condition: template
#             value_template: '{{is_state(''sensor.chargeamps_let_charge'', ''Done'')}}

#               '
#           sequence:
#           - service: input_boolean.turn_on
#             target:
#               entity_id: input_boolean.chargeamps_charging_done
#         default: []
#       - service: chargeamps.disable
#       - delay:
#           hours: 0
#           minutes: 2
#           seconds: 0
#           milliseconds: 0
#       - service: chargeamps.set_max_current
#         data:
#           max_current: 6
#   - choose:
#     - conditions:
#       - condition: state
#         entity_id: input_boolean.chargeamps_charging_done
#         state: 'on'
#       sequence:
#       - service: script.turn_on
#         target:
#           entity_id: script.notify_people_that_are_home
#         data:
#           variables:
#             title: Huset
#             message: Bilen är färdigladdad.
#     default:
#     - delay:
#         hours: 0
#         minutes: 1
#         seconds: 0
#         milliseconds: 0

#   mode: restart
        pass
  
    def UpdateMaxCurrent():
        while constants.CHARGER["state"] == "Charging":
            pass
#   trigger:
#   - platform: state
#     entity_id: sensor.hake_2012019145m_1
#     to: Charging
#   condition: []
#   action:
#   - repeat:
#       while:
#       - condition: state
#         entity_id: sensor.hake_2012019145m_1
#         state: Charging
#       sequence:
#       - wait_template: '{{(((state_attr(''switch.hake_2012019145m_1'',''max_current'')|int
#           < states(''sensor.chargeamps_allowed_current_new'')|int) and now().minute
#           < 55) or (state_attr(''switch.hake_2012019145m_1'',''max_current'')|int
#           > states(''sensor.chargeamps_allowed_current_new'')|int)) and states(''sensor.utility_total_energy_hourly'')|float
#           > 0 and states(''sensor.chargeamps_allowed_current_new'')|int > 0}}'
#       - service: chargeamps.set_max_current
#         data:
#           max_current: '{{states(''sensor.chargeamps_allowed_current_new'')|int}}'
#       - delay:
#           hours: 0
#           minutes: 3
#           seconds: 0
#           milliseconds: 0
#   mode: restart
        pass



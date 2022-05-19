[![hacs_badge](https://img.shields.io/badge/HACS-Default-brightgreen.svg)](https://github.com/hacs/integration) 
![Validate with hassfest](https://github.com/elden1337/hass-peaq/workflows/Validate%20with%20hassfest/badge.svg) 
[![Peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/total)](https://github.com/elden1337/hass-peaq) 
[![hass-peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/latest/total)](https://github.com/elden1337/hass-peaq)
[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&message=🥨&color=black&logo=buy%20me%20a%20coffee&logoColor=white&labelColor=6f4e37)](https://www.buymeacoffee.com/elden)
# Peaqev ev-charging

![Peaq logo](https://raw.githubusercontent.com/elden1337/hass-peaq/main/assets/icon.png)

Peaqev ev-charging is an attempt of charging an ev without breaching a preset monthly max-peak energy level. 
In order for this integration to function, you will need to have a sensor/device that reads your current power-draw with good resolution *examples below*. You will also have to disable any other smart-charging capability you may have, such as scheduled charging or energy-price-aware charging, the latter will come as parameter here in a future update.

This integration does not communicate with any properitary API's, everything is handled locally in your Home Assistant. However, the chargers selected will use the integrations set for them, and may include cloud polling of data.

*While this integration will try to not break your monthly energy peak hour, there is off course no guarantee. Various factors beyond control of this logic do occur, so for those aiming at staying below their threshold, I do suggest you think about the non-hours, caution-hours etc in the setup. These hours should be set when you commonly utilize a lot of extra energy in your home, such as cooking, doing laundry etc.* 

## Installation
*Required to install is Home Assistant version 2022.4.5 or higher.*

Preferred if you have HACS installed is to search for Peaqev there.

Otherwise you may:
- Copy `custom_components/peaqev` folder to `<config_dir>/custom_components/peaqev/`
- Restart Home assistant
- Go to Configuration > Devices & Services > Add integration

### Config setup:

Peaqev has two types of installations: Regular and Lite. Regular is much more precise, but requires an installed powersensor.

[![](https://mermaid.ink/img/pako:eNpVkNtqwzAMhl_F-CqD5gVyMRg5NIUMRrO7eRciVhuDYwdFZpSm7z7nUNh0Jen_pB_pLjuvUWbySjD2ojkrJ2K8fbUMxN8iTV9FnpzcxGAtsPFO8G3Elw3LF31uDOMsiiTvga5IApwWje_A_sfOeA0WaBZl0qKbPO1quZoUW1GsRZV8kOkwhR-g55JqXVKBnaLZMal9oGmXjutQ_Zf7pBCxOnn3jvuFU7zJ8iAHpAGMjkffl56S3OOASmYx1XiBYFlJ5R4RDaMGxlIb9iSzy2J-kBDYtzfXyYyjyxMqDMQfDjv1-AUWBWqX)](https://mermaid-js.github.io/mermaid-live-editor/edit#pako:eNpVkNtqwzAMhl_F-CqD5gVyMRg5NIUMRrO7eRciVhuDYwdFZpSm7z7nUNh0Jen_pB_pLjuvUWbySjD2ojkrJ2K8fbUMxN8iTV9FnpzcxGAtsPFO8G3Elw3LF31uDOMsiiTvga5IApwWje_A_sfOeA0WaBZl0qKbPO1quZoUW1GsRZV8kOkwhR-g55JqXVKBnaLZMal9oGmXjutQ_Zf7pBCxOnn3jvuFU7zJ8iAHpAGMjkffl56S3OOASmYx1XiBYFlJ5R4RDaMGxlIb9iSzy2J-kBDYtzfXyYyjyxMqDMQfDjv1-AUWBWqX)

##### Installation type:
- `Installation type` - Pick regular for the full Peaqev-experience. This will charge according to your home's total energy. Pick Lite if you do not have such a sensor installed. Peaqev will then charge the allowed hourly amount set further down in "Months"

##### Sensor:
- `Power sensor` - The already existing power sensor in your setup. This is required to get the reading to work. Examples of devices sending such data is Tibber Pulse/Watty, Shelly DIN-mounted devices or similar.
- `Power sensor includes car` - Check this option if the above sensor includes your car's power draw. The calutions will be altered accordingly

##### Charger and Locale:
- `City, or Grid owner company` - Chose your city from the list. The characteristics differ in how peak hours are stored and measured. If you don't live in a supported location but just want to test the integration, or lower your peaks for other reasons, you may check *"Other, just want to test"*
- `Charger type` - Pick the installed ev-charger you have. Currently Chargeamps and Easee are supported. Check links for required custom components per charger-type: [Chargeamps](https://github.com/kirei/hass-chargeamps), [Easee](https://github.com/fondberg/easee_hass/)
- `Charger id` - Your local identifier to tell Peaqev which charger unit we mean to manipulate. If your chargertype does not provide this, leave blank

##### Price-aware:
- `Price aware charging` - Check this to calculate the cheapest hours from Nordpool (requires [Nordpool](https://github.com/custom-components/nordpool)). Above Non- and Caution-hours will be ignored.
- `Absolute top price` - The limit (if any) where your charger should be stopped, regardless of the hour-algorithm.
- `Caution-hour type` - Choose to what extent you would like Peaqev to hold back during caution-hours. *Suave > Aggressive* 

##### Hours:
- `Non hours` - Click to select the hours (if any) where you do not wish to charge.  
- `Caution hours` - Click to select the hours (if any) where you want the charger to be extra cautious to not break the peak.

##### Months:
- `Monthly allowed peak` - Needs to be set in order to determine a minimum allowed peak. In the beginning of each month this is necessary to be able to charge at all. *Format is in kW. See examples below*


These are two (quite restrained) examples of monthly start peaks, for 1-phase and 3-phase charging respectively. This option is always up to your house and it's other appliances. The below are made for a modern house with installed heat pump.
These suggestions are also made for hourly calculation. Should your Locale apply other, like quarter-hourly, do consider altering the numbers accordingly.

Month | 1-phase charge | 3-phase charge
--- | --- | ---
Jan| 2.0 | 4.0
Feb| 1.8 | 3.6
Mar| 1.8 | 3.6
Apr| 1.5 | 3.0
May| 1.5 | 3.0
Jun| 1.5 | 3.0
Jul| 1.5 | 3.0
Aug| 1.5 | 3.0
Sep| 1.5 | 3.0
Oct| 1.5 | 3.0
Nov| 1.8 | 3.6
Dec| 2.0 | 4.0

### Locale

#### Belgium

Locale | Characteristics
--- | ---
Belgium (VREG) | single monthly max peak is used in calculation, but the energy is cycled quarter-hourly instead of hourly. 


#### Sweden

Locale | Characteristics
--- | --- 
Gothenburg, Sweden | The average of three max peak hours from different days is what your are charged for. The algorithm tries to stay below the minimum value of these three peaks.
Karlstad, Sweden | single max peak
Kristinehamn, Sweden | for Nov-Mar, max peak during Mon-Fri 07-17. Other months, single max peak
Malung-Sälen, Sweden | Average of five peaks on different days. Peaks are calc between 07-19. Other hours are free-charge.
Nacka, Sweden (Normal tariffe) | The average of three max peak hours is what your are charged for. The algorithm tries to stay below the minimum value of these three peaks.
Other, just want to test | Single monthly peak hour is what is being avoided by the algorithm
Partille, Sweden | Single monthly peak hour is what is being avoided by the algorithm
Sala, Sweden (SHE ab-customer) | The average of three max peak hours, that do occur Mon-Fri, between 07-19. Other hours are non-observed.
Skövde, Sweden | Single monthly max peak. Observed Nov-Mar, Mon-Fri between 06-22. Other hours are non-observed. 
Sollentuna, Sweden | Average of three hours, workdays between 7-19.


*More cities will come in future updates*

## Usage

- To start and stop, I suggest you create automations that call the services `peaqev.enable` and `peaqev.disable`. 
- Make sure to not exclude the created sensors from your recorder, as this would conflict with the monthly peaks.

Example of basic automations to enable/disable the charging. Your states here may differ from the example which is a Chargeamps Halo:
```yaml
- id: '111111'
  alias: Peaq - Charge
  trigger:
  - platform: state
    entity_id: sensor.your_chargersensor
    from: Available
    to: Connected
  - service: peaqev.enable
    data: {}
  mode: single

- id: '222222'
  alias: Peaq - Disconnected
  trigger:
  - platform: state
    entity_id: sensor.your_chargersensor
    to: Available
  condition: []
  action:
  - service: peaqev.disable
    data: {}
  mode: single
```

*Tested with Chargeamps Halo 11kw and Easee. Both setups with one single charger per household. Currently will not function where multiple chargers have been installed ,2022-05-16*



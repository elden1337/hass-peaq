[![hacs_badge](https://img.shields.io/badge/HACS-Default-brightgreen.svg)](https://github.com/hacs/integration) 
![Validate with hassfest](https://github.com/elden1337/hass-peaq/workflows/Validate%20with%20hassfest/badge.svg) 
[![Peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/total)](https://github.com/elden1337/hass-peaq) 
[![hass-peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/latest/total)](https://github.com/elden1337/hass-peaq)


# Peaqev ev-charging

<img src="https://raw.githubusercontent.com/elden1337/hass-peaq/main/assets/icon.png" width="125">

### :cherries: Sponsorship and prioritized development :cherries:
Peaqev is developed without static funding. If you lack your locale/charger type or have wishes for other specific features that you would like to see prioritized, please consider becoming a [Github sponsor](https://github.com/sponsors/elden1337) to bump your desired changes in my backlog.
- In order to flag a ticket, either create a new one or comment on an existing one after you've started your sponsorship. I will then flag the ticket with `sponsored-change` and try to prioritize this going forward
- Becoming a sponsor is not a guarantee that a wish will be created, or a guarantee for a specified resolution time. Peaqev is being developed in my spare time and every feature has to be considered by me before taking it into development
- I may need to reach out for testing, especially if your wish includes implementing new charger types
- Critical bugs discovered of course always triages higher than features

:love_letter:

---

Peaqev aims at lowering the household's peak energy charges, targeted at charging an electronic vehicle (EV) below a set threshold. 
Peaqev covers 24 different energy companies in Sweden, Norway and Belgium and two types of ev chargers _(2021-11-03)_
You will get the best experience with a supported charger that can update amps while charging, as well as using a connected power meter that update your total power draw frequently. Examples of such meters are:

- Shelly 3EM
- Tibber Watty
- Tibber Pulse


The integration does not communicate with any properitary API's. However, the chargers selected will use the integrations set for them, and may include cloud polling of data.

For usage-examples and more in-depth explanations, see the Wiki:
* [List of available Locales](https://github.com/elden1337/hass-peaq/wiki/Locale)
* [Price awareness](https://github.com/elden1337/hass-peaq/wiki/Price-awareness)
* [Scheduler](https://github.com/elden1337/hass-peaq/wiki/Scheduler)
* [Usage](https://github.com/elden1337/hass-peaq/wiki/Usage)

## Installation
*Required to install is Home Assistant version 2022.10.5 or higher.*

Preferred if you have HACS installed is to search for Peaqev there.

Otherwise you may:
- Copy `custom_components/peaqev` folder to `<config_dir>/custom_components/peaqev/`
- Restart Home assistant
- Go to Configuration > Devices & Services > Add integration

### Config setup:

Peaqev has two types of installations: Regular and Lite. Regular is much more precise, but requires an installed power sensor while Lite does not.

[![](https://mermaid.ink/img/pako:eNpVkNtqwzAMhl_F-CqD5gVyMRg5NIUMRrO7eRciVhuDYwdFZpSm7z7nUNh0Jen_pB_pLjuvUWbySjD2ojkrJ2K8fbUMxN8iTV9FnpzcxGAtsPFO8G3Elw3LF31uDOMsiiTvga5IApwWje_A_sfOeA0WaBZl0qKbPO1quZoUW1GsRZV8kOkwhR-g55JqXVKBnaLZMal9oGmXjutQ_Zf7pBCxOnn3jvuFU7zJ8iAHpAGMjkffl56S3OOASmYx1XiBYFlJ5R4RDaMGxlIb9iSzy2J-kBDYtzfXyYyjyxMqDMQfDjv1-AUWBWqX)](https://mermaid-js.github.io/mermaid-live-editor/edit#pako:eNpVkNtqwzAMhl_F-CqD5gVyMRg5NIUMRrO7eRciVhuDYwdFZpSm7z7nUNh0Jen_pB_pLjuvUWbySjD2ojkrJ2K8fbUMxN8iTV9FnpzcxGAtsPFO8G3Elw3LF31uDOMsiiTvga5IApwWje_A_sfOeA0WaBZl0qKbPO1quZoUW1GsRZV8kOkwhR-g55JqXVKBnaLZMal9oGmXjutQ_Zf7pBCxOnn3jvuFU7zJ8iAHpAGMjkffl56S3OOASmYx1XiBYFlJ5R4RDaMGxlIb9iSzy2J-kBDYtzfXyYyjyxMqDMQfDjv1-AUWBWqX)

##### Installation type:
- `Installation type` - Pick Lite if you do not have a power meter installed. Peaqev will then charge the allowed hourly amount set further down in "Months". Otherwise pick Regular

##### Sensor:
- `Power sensor` - The wattage reading sensor for your connected powermeter. Must be in Watts (W)
- `Power sensor includes car` - Check this option if the above sensor includes your car's power draw

##### Charger and Locale:
- `City, or Grid owner company` - The characteristics differ in how peak hours are stored and measured
- `Charger type` - Pick the installed ev charger you have. _Check table below for for required custom component and features per charger type_
- `Charger id` - Your local identifier to tell Peaqev which charger unit we mean to manipulate. If your charger type does not provide this, leave blank
- *If you have selected Smart outlet as charger type, you will need to provide the switch to turn on/off, and the sensor to read power from the outlet instead of charger id.*

Charger | Required integration | Can update amps | Supported models | Notes
--- | --- | --- | --- | ---
Chargeamps| [hass-chargeamps](https://github.com/kirei/hass-chargeamps) | Yes | Halo |
Easee| [easee-hass](https://github.com/fondberg/easee_hass/) | Yes | Robot | _Turn off all smart charging before using peaqev_
Smart outlet| - | No | | _Stability depends on the outlet used_


##### Price-aware:
- `Price-aware charging` - Check this to calculate the cheapest hours from Nordpool (requires [Nordpool](https://github.com/custom-components/nordpool)). Non- and Caution hours below here will be ignored
- `Absolute top price` - The limit (if any) where your charger should be stopped, regardless of the hour algorithm
- `Min price` - The lower limit (if any) where charging will always be permitted (must be lower than top price if set)
- `Caution hour type` - Choose to what extent you would like Peaqev to hold back during caution hours. *Suave > Aggressive* 

##### Hours:
- `Non hours` - Click to select the hours (if any) where you do not wish to charge
- `Caution hours` - Click to select the hours (if any) where you want the charger to be extra cautious to not break the peak

##### Months:
- `Monthly allowed peak` - Needs to be set in order to determine a minimum allowed peak. In the beginning of each month this is necessary to be able to charge at all. *Format is in kW. See examples below*


Examples for hourly peak-shaving. A tip is to look at your current peaks and set it to about 50-70% of those.

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


*While this integration will try to not break your monthly energy peak hour, there is off course no guarantee. Various factors beyond control of this logic do occur, so for those aiming at staying below their threshold, I do suggest you think about the non-hours, caution-hours etc in the setup. These hours should be set when you commonly utilize a lot of extra energy in your home, such as cooking, doing laundry etc.*

-----

A special thanks to my sponsors! Your support is greatly appreciated. 
- [@mejje](https://github.com/mejje)

> 2024-10-08
> 
> Dear Peaquser,
> 
> After three years of open source in these projects, I am about to set sail on the next leg of my journey.
> I will soon start a job where I will work with adjacent technology, and thus will seize to update the repos with new features.
> This is to not be questioned regarding IP going forward.
> 
> For the time being I want to let the codebases stay online, and will accept pull requests and occasionally do patch updates and bug fixes to > keep the solutions running.
> However, I will not take part in general feature discussions any longer, starting from 2024-11-01.
> 
> If you wish you may fork the projects and create features that you send me as pull requests. That way we can keep the flow going without > my direct interference in the inventions.
> For any usage not covered by the general download by hacs, look towards the license on the repos for guidance. Here's a snapshot of what > the licenses on my code requires: https://creativecommons.org/licenses/by-nc-nd/4.0/deed.en
> 
> Thanks for all engagement and happy to have helped a bunch of people with this spare time invention of mine. 
> //Magnus

<img src="https://raw.githubusercontent.com/creativecommons/cc-assets/main/license_badges/big/by_nc_nd.svg" width="90">

[![Peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/total)](https://github.com/elden1337/hass-peaq)
[![hass-peaq_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaq/latest/total)](https://github.com/elden1337/hass-peaq)
[![Paypal](https://img.shields.io/badge/Sponsor-PayPal-orange.svg)](https://www.paypal.com/donate/?hosted_button_id=GLGW8QAAQC2FG)
[![BuyMeACoffee](https://img.shields.io/badge/Sponsor-BuyMeACoffee-orange.svg)](https://buymeacoffee.com/elden)
[![Discord](https://img.shields.io/badge/Join-Discord-green.svg)](https://discord.gg/kgZzdsf4XA)

# Peaqev ev-charging


<img src="https://raw.githubusercontent.com/elden1337/hass-peaq/main/assets/icon.png" width="125">

First time here? Check the [getting-started](https://github.com/elden1337/hass-peaq/wiki/Getting-started)

Interested in sponsoring or prioritizing a certain feature, look [here](https://github.com/elden1337/hass-peaq/wiki/Sponsorship-and-prioritized-development)

Peaqev aims at lowering the household's peak energy charges, targeted at charging an electronic vehicle (EV) below a dynamic threshold.
Peaqev covers [28 different energy companies](https://github.com/elden1337/hass-peaq/wiki/Locale) in Sweden, Norway and Belgium.
You will get the best experience with a supported charger that can update amps while charging, as well as using a connected power meter that update your total power draw frequently (every 10s or more).
_Peaqev can also be used without living in an area with peak-shaving implemented, you may utilize it soley for the purpose of charging at the lowest available hours in your area (Requires Nordpool)_

The integration does not communicate with any proprietary API's. However, the chargers selected will use the integrations set for them, and may include cloud polling of data.

For usage-examples and more in-depth explanations, see the Wiki:
* [List of available Locales](https://github.com/elden1337/hass-peaq/wiki/Locale)
* [Price awareness](https://github.com/elden1337/hass-peaq/wiki/Price-awareness)
* [Scheduler](https://github.com/elden1337/hass-peaq/wiki/Scheduler)
* [Usage](https://github.com/elden1337/hass-peaq/wiki/Usage)

## Installation
*Required to install is Home Assistant version 2024.7.1 or higher.*

Preferred if you have HACS installed is to search for Peaqev there.

Otherwise you may:
- Copy `custom_components/peaqev` folder to `<config_dir>/custom_components/peaqev/`
- Restart Home assistant
- Go to Configuration > Devices & Services > Add integration

### Config setup:

Peaqev has two types of installations: Regular and Lite. Regular is much more precise, but requires an installed power sensor while Lite does not.


[![](https://mermaid.ink/img/pako:eNpVkEFrwzAMhf-K0cmDht1zGIwkbQYpjGa3eQcRq4lZEgfFZpSm_32u0wzmk_S9ZyG9KzRWE6TQMk6dqE5qFOG9ftYO2X2JJHkRmfy4TPS0KtkdLZVxtIhcZh1yS_xc2Qb7_5YTtb5HXkQhaxpnyw-1iDPztcljs5fvbBpK8Ad5G7KPykGW1vP8YIfIShl3mwi_N6GMwps8mrkJSLkVww4G4gGNDgde70yB62ggBWkoNZ3R906BGm_B6ieNjgptnGVIz9jPtAP0ztaXsYHUsafNlBsMeQ1_LoqfjmuSMdDbLwiTaMQ?type=png)](https://mermaid-js.github.io/mermaid-live-editor/edit#pako:eNpVkEFrwzAMhf-K0cmDht1zGIwkbQYpjGa3eQcRq4lZEgfFZpSm_32u0wzmk_S9ZyG9KzRWE6TQMk6dqE5qFOG9ftYO2X2JJHkRmfy4TPS0KtkdLZVxtIhcZh1yS_xc2Qb7_5YTtb5HXkQhaxpnyw-1iDPztcljs5fvbBpK8Ad5G7KPykGW1vP8YIfIShl3mwi_N6GMwps8mrkJSLkVww4G4gGNDgde70yB62ggBWkoNZ3R906BGm_B6ieNjgptnGVIz9jPtAP0ztaXsYHUsafNlBsMeQ1_LoqfjmuSMdDbLwiTaMQ)

#### Installation type:
- `Installation type` - Pick Lite if you do not have a power meter installed. Peaqev will then charge the allowed hourly amount set further down in "Months". Otherwise pick Regular

#### Sensor:
- `Power sensor` - The wattage reading sensor for your connected powermeter. Must be in Watts (W)
- `Power sensor includes car` - Check this option if the above sensor includes your car's power draw

#### Charger and Locale:
- `City, or Grid owner company` - The characteristics differ in how peak hours are stored and measured
- `Charger type` - Pick the installed ev charger you have. _Check table below for required custom component and features per charger type_
- `Charger id` - Your local identifier to tell Peaqev which charger unit we mean to manipulate. If your charger type does not provide this, leave blank
- *If you have selected Smart outlet as charger type, you will need to provide the switch to turn on/off, and the sensor to read power from the outlet instead of charger id.*

Charger | Required integration                                        | Can update amps | Supported models | Notes
--- |-------------------------------------------------------------| --- | --- | ---
Chargeamps| [hass-chargeamps](https://github.com/kirei/hass-chargeamps) | Yes | Halo, Aura (plug 1) |
Easee| [easee-hass](https://github.com/fondberg/easee_hass/)       | Yes | Robot | _Turn off all smart charging before using peaqev_
Zaptec| [zaptec](https://github.com/custom-components/zaptec)       | No | Go | _Currently in beta and may not work_
Garo|[garo_wallbox](https://github.com/sockless-coding/garo_wallbox/)       | No | Wallbox | _Currently in beta and may not work_
Wallbox|[wallbox](https://www.home-assistant.io/integrations/wallbox/)       | No | * | _Currently in beta and may not work_
Smart outlet| -                                                           | No | | _Stability depends on the outlet used_
No charger| - | No | | _For using the sensors and logic_


#### Price-aware:
- `Price-aware charging` - Check this to calculate the cheapest hours from [Nordpool](https://github.com/custom-components/nordpool) or [EnergiDataService](https://github.com/MTrab/energidataservice). Non- and Caution hours below here will be ignored
- `Dynamic top price` - If checked, the absolute top price for charging will be calculated by the monthly average from the spotprice-source (current month)
- `Absolute top price` - The limit (if any) where your charger should be stopped, regardless of the hour algorithm
- `Min price` - The lower limit (if any) where charging will always be permitted (must be lower than top price if set)
- `Caution hour type` - Choose to what extent you would like Peaqev to hold back during caution hours. *Suave > Aggressive*

#### Hours:
- `Non hours` - Click to select the hours (if any) where you do not wish to charge
- `Caution hours` - Click to select the hours (if any) where you want the charger to be extra cautious to not break the peak

#### Months:
- `Monthly allowed peak` - Needs to be set in order to determine a minimum allowed peak. In the beginning of each month this is necessary to be able to charge at all. *Format is in kW. See examples below*

#### Experimental and extra options:
- `Main fuse` - (optional) Pick your main fuse setup to allow peaqev to detect and stop charging if consumption is about to breach the limit

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


*While this integration will try to not break your monthly energy peaks, there is off course no guarantee. Various factors beyond control of this logic do occur, so for those aiming at staying below their threshold, I do suggest you think about the non-hours, caution-hours etc in the setup. These hours should be set when you commonly utilize a lot of extra energy in your home, such as cooking, doing laundry etc.*

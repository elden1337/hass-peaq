# peaq ev-charging

bla bla bla introduction

## Installation

- Copy this folder to `<config_dir>/custom_components/peaqev/` or install via HACS.

### Config setup:

Search for peaqev in your integrations setup. Fill in the following parameters:

- `Power sensor` - The already existing power sensor in your setup. This is vital 
- `Power sensor includes car` - Check this option if the above sensor includes your car's power draw. The calutions will be altered accordingly
- `Locale` - Chose your city from the list. The characteristics differ in how peak hours are stored and measured. If you don't live in a supported location but just want to test the integration, or lower your peaks for other reasons, you may check *"Other, just want to test"*
- `Charger type` - Pick the installed ev-charger you have. Currently Chargeamps and Easee are supported. 
- `Non hours` - Click to select the hours (if any) where you do not wish to charge.  
- `Caution hours` - Click to select the hours (if any) where you want the charger to be extra cautious to not break the peak. 
- `Monthly allowed peak` - Needs to be set in order to determine a minimum allowed peak. In the beginning of each month this is necessary to be able to charge at all. *Format is in kW. See examples below*

These are two (quite restrained) examples of monthly start peaks, for 1-phase and 3-phase charging respectively. This option is always up to your house and it's other appliances. The below are made for a modern house with installed heat pump.

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


Locale | Characteristics
--- | ---
Gothenburg, Sweden | The average of three max peak hours from different days is what your are charged for. The algorithm tries to stay below the minimun value of these three peaks.
Partille, Sweden | Single monthly peak hour is what is being avoided by the algorithm
Other, just want to test | Single monthly peak hour is what is being avoided by the algorithm


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

*Tested with Chargeamps Halo 11kw and Easee. Both setups with one single charger per household. Currently will not function where multiple chargers have been installed ,2022-04-01*



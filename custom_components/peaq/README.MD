# peaq

bla bla bla introduction

### Installation

- Copy this folder to `<config_dir>/custom_components/peaq/` or install via HACS.
- Setup via regular Integrations, search for "Peaq ev-charging"

Config:
```yaml
    
    power sensor: sensor.current_power #Required. This is what give us the option of calculating peaks
    power_includes_car: false #Important! Defaults to false, but if your car power is included in the sensor you need to add a true here.
    locale: SE_Gothenburg #See list below. This determines your peak energy charges to be avoided
    charger type: Easee or Chargeamps
```

Options:
```yaml
    non_hours: [16,17] #optional. If any, the charging will not be allowed during these hours (when service is on)
    caution_hours: [1,2,3] #optional. If any, the charge thresholds will be lowered during these hours (when service is on)
    monthly_allowed_peak: {1: 2.0, 2: 1.8, 3: 1.8, 4: 1.5, 5: 1.5, 6: 1.5, 7: 1.5, 8: 1.5, 9: 1.5, 10: 1.5, 11:1.8, 12: 2.0} #needs to be set in order to determine a minimum allowed peak. In the beginning of each month this is necessary to be able to charge at all.
    nordpool_adjust: false #to be implemented. If true the charging will try to compare current grid pricing vs peak charges and give you the best alternative.
```

### Usage

Bla bla call the service from an automation. 
bla bla make sure to store the statistics in your recorder for at least 31 days.

Tested with Chargeamps Halo 11kw and Easee. Both setups with one single charger per household. Currently will not function where multiple chargers have been installed [2022-04-01]


Locale | Characteristics
--- | ---
SE_Gothenburg | 301
SE_Karlstad | 301
SE_Kristinehamn | 301
SE_Nacka | 301
SE_Partille | 301


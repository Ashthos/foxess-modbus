# Python Script for Charge Time

## Overview

This python script has been written to be run within Home Assistant. It uses sensor data to determine how much time the battery must charge in order
for it to ensure that either:

1. The minimum SoC is not breached during the day
2. A target SoC can be reached during the day
3. There is no 'excess' solar energy generated

## Installation

1. Create a directory `python_scripts` in the same directory as your `configuration.yaml`
2. Create a file named `calculate_fox_charge.py` in the `python_scripts` directory
3. Add `python_script: !include_dir_merge_list python_scripts/` into `configuration.yaml` to load the script.
4. Restart Home Assistant

## Configuration

You can modify the values at the top of the script to alter the calculations the script performs.

Doing so will mean you do not have to invoke the script with any `data: {}` values. 

`batteryTargetChargePercent` - The target SoC% for the battery during the day, normally this will be `100`%, but you may want to have this lower (?)
`batteryCapacity` - The battery capacity in Watts. So 10kwh = `10400`
`batteryChargeRate` - The charge rate of the battery from the grid in Watts. So 2.3kw = `2300`
`batteryMinChargePercent` - The minimum SoC desired for the battery. This may be the same as the configured Min SoC for the inverter, or it may be more.
`houseBaseload` - The 'normal' base load for the house in Watts. Imagine this as being the normal house usage of power when away.
`cheapRateElectricityStart` - Hour:Minute when the Cheap rate electricity starts
`cheapRateElectricityEnd` - Hour:Minute when the Cheap rate electricity ends

## Invoking the Script

Invoke the script using the values configured in the script by calling the service with a blank data object.

```
service: python_script.calculate_fox_charge
data: {}
```

To override one of the configured values, pass the corresponding values in the data.

```
service: python_script.calculate_fox_charge
data: {
  targetSoc: 95,
  batteryCapacity: 5100,
  batteryChargeRate: 1000,
  batteryMinChargePercent: 25,
  houseBaseload: 423,
  cheapRateElectricityStart: "00:00",
  cheapRateElectricityEnd: "06:45"
}
```

## Script Output

The script populates a sensor value with data when it completes. Use this value to determine how long the battery should charge.

`sensor.battery_charge_required_minutes`

### Attributes

The sensor value also has attributes that could help determine other behaviour to follow:

```
required_soc_extra: 0
calculated_date: '2023-03-25T19:03:16.564598'
minimum_soc_no_charge: 48
maximum_soc: 65
target_battery_hour: -1
mins_for_target: 92
excess_solar: 0
```

`required_soc_extra` - The amount of extra charge required to ensure the battery does not fall below the minimum threshold before the next charge happens
`calculated_date` - The date time the script was run and the values calculated. If this is a long time in the past then don't trust these values to set the charge time.
`minimum_soc_no_charge` - The minimum SoC the battery will reach before the next charge time if no charge happens.
`maximum_soc` - The maximum SoC the battery will reach before the next charge time (assuming the predicted solar goes to charge the battery)
`target_battery_hour` - The hour of the day that the battery first reaches the target Soc. If -1 then it won't reach the target (without charging)
`mins_for_target` - The number of minutes of charge required, given the current SoC and predicted solar, for the target SoC to be reached.
`excess_solar` - The expected solar excess in Watts, when the target SoC has been met. Assumes no charge added to battery.

## Sensor value use in Home Assistant

To call the set_charge_time rest call using the charge time state:

```
service: rest_command.set_charge_time
data:
  start_time: >-
    {{
    ((state_attr('schedule.cheap_rate_electricity','next_event')).strftime('%s')
    | int) | timestamp_custom('%H:%M', false) }}
  end_time: >-
    {{
    (((state_attr('schedule.cheap_rate_electricity','next_event')).strftime('%s')
    | int + (states("sensor.battery_charge_required_minutes") | int * 60)) |
    timestamp_custom('%H:%M', false)) }}
```

To use the `mins_for_target` attribute for charge timing:

```
service: rest_command.set_charge_time
data:
  start_time: >-
    {{
    ((state_attr('schedule.cheap_rate_electricity','next_event')).strftime('%s')
    | int) | timestamp_custom('%H:%M', false) }}
  end_time: >-
    {{
    (((state_attr('schedule.cheap_rate_electricity','next_event')).strftime('%s')
    | int + (state_attr("sensor.battery_charge_required_minutes", "mins_for_target") | int * 60)) |
    timestamp_custom('%H:%M', false)) }}
```

## Use Cases

1. Default `sensor.battery_charge_required_minutes`

The most basic use case, and that which is supported by the main sensor value, is to REDUCE the amount of grid electricity put into the battery during 
cheap rate electricity periods, but still ensure that the battery does not drop below the minimum SoC (which may well force a charge from the Grid at
an expensive rate).

This scenario assumes that the script will be re-run just before the next cheap rate charge period and so will then charge the battery if necessary.

This behaviour ONLY covers the base load of the house. Almost as if you are away and no-one is at home. It will minimise the amount of electricity drawn 
from the grid and ensure it is cheap rate.

2. Cover electricity usage during occupancy

When the house is in use, it can be assumed that there will be more electricity used than the absolute base load. In this scenario, it is better to 
'fill' the battery with cheap rate electricity which will be used during expensive rate periods. 

Additionally, it is desirable to use 'free' solar power instead of (cheap rate) electricity from the grid, so prefer to fill the battery less during
cheap rate periods if the solar is likely to take the charge up to (or beyond) the target.

Use the `mins_for_target` attribute values to determine how long to charge - so the battery reaches the target during the day.

3. Maximising Solar Usage

If the desire is to deliver no electricity to the grid from Solar (feed-in), it may be necessary to charge the battery to get through the night, but 
then artifically use energy at certain times ensure that the target SoC is only just reached by solar generation.

For those with a 'dump load' that can draw electricity down consistently (like charging an EV, or using an immersion heater), these can be automated
to draw the battery SoC down to a position where almost all the solar generation will be consumed returning the battery to the target SoC.

This scenario has additional complexity in that if charge is required to ensure the minimum SoC is not breached, the charge added to the battery
is not included in the `excess_solar` value and so it will be necessary to draw more power from the battery to account for this.

Use the `excess_solar` and `target_battery_hour` values to determine how many watts to draw from the battery before the `target_battery_hour` time.

## Useful(?) commentary

The numbers generated by this script should be used in addition to your own knowledge of your system and other sensor values. 

Smaller batteries may be harder to 'manage' than larger ones, as minimum and maximum values may be reached quickly. A 'small' battery is always relative
to the size (and efficiency) of the solar array supplying it. A big battery with a massive array will be even harder to control.

Use other sensor values (such as the Solcast 'Solar Remaining Today') values to double check this scripts numbers. If the script is run after sunset, 
but before midnight, its numbers will be close to useless (sorry to those whos cheap rate bridges midnight).

Solar forecasts have a margin of error to their numbers, adjust your expectations (and min/max values) accordingly.

The script cannot take into account 'ad-hoc' loads. Use of such things as electric ovens, heaters etc will impact the speed at which the Minimum SoC
may be reached. It may be wise to start with overly cautious Min SoC values and adjust as the system proves itself and you understand the risks.
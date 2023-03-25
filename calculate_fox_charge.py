batteryTargetChargePercent = int(data.get("targetSoc", 100))
batteryCapacity = int(data.get("batteryCapacity", 10400))
batteryChargeRate = int(data.get("batteryChargeRate", 2367))
batteryMinChargePercent = int(data.get("batteryMinChargePercent", 20))
houseBaseload = int(data.get("houseBaseload", 350))
cheapRateElectricityStart = data.get("cheapRateElectricityStart", "00:30")
cheapRateElectricityEnd = data.get("cheapRateElectricityEnd", "04:30")

# If the current time is after cheapRateElectricityEnd then terminate the script
now = datetime.datetime.now()
logger.info("now %s", now)

cheapRateElectricityEndParts = cheapRateElectricityEnd.split(":")

#if int(cheapRateElectricityEndParts[0]) > now.hour:
#    return
    
#if int(cheapRateElectricityEndParts[0]) == now.hour and int(cheapRateElectricityParts[1]) > now.minute:
#    return

stateOfChargeEntity = data.get("stateOfChargeEntity", "sensor.battery_soc")
solarForecastEntity = data.get("solarForecastEntity", "sensor.solcast_forecast_today") # Valid if run right after Midnight, otherwise will need to be forecast_tomorrow

solarForecastData = hass.states.get(solarForecastEntity).attributes.get("forecast")
batteryCurrentSoc = int(hass.states.get(stateOfChargeEntity).state)

# Calculate the maximum the battery can be drained from its current state.
batteryMaxDrain = batteryCurrentSoc - batteryMinChargePercent

# From now in the forecasts, work forwards and see if we hit either the min or max (100) soc
# Only care about the first Min/Max event, as that is the only one we can infulence.


logger.info("==========================================================================")
logger.info("= Calculating battery recharge time required")
logger.info("==========================================================================")

calculatedBatterySoc = batteryCurrentSoc
minimumSoc = batteryCurrentSoc
maximumSoc = 0
targetSocAt = -1
toTargetSocMinutes = 0
excessWatts = 0

# logger.info("calculatedBatterySoc %s", calculatedBatterySoc)

for forecastEntry in solarForecastData:
    forecastTime = forecastEntry["period_start"].time()    # '2022-11-20T00:00:00+00:00' -> '00:00:00+00:00'
    timeNow = now.time()
    percentLeftOfHour = 0.0
    
    if timeNow.hour < forecastTime.hour + 1:
        percentLeftOfHour = 1.0
        
    if timeNow.hour == forecastTime.hour:
        logger.info("Part way through current hour. Adjusting delta.")
        percentLeftOfHour = 1 - ((100 / (60 / timeNow.minute)) / 100)
        
    delta = (float(forecastEntry["pv_estimate"]) * percentLeftOfHour) - (houseBaseload * percentLeftOfHour)
    deltaSoc = (100 / batteryCapacity) * delta
    
    #logger.info("forecastTime %s", forecastTime)
    #logger.info("delta %s", delta)
    #logger.info("deltaSoc %s", deltaSoc)
    
    calculatedBatterySoc = calculatedBatterySoc + deltaSoc
    #logger.info("calculatedBatterySoc %s", calculatedBatterySoc)
    if calculatedBatterySoc < minimumSoc:
        minimumSoc = calculatedBatterySoc
        
    if calculatedBatterySoc > maximumSoc:
        maximumSoc = calculatedBatterySoc
    
    if calculatedBatterySoc >= batteryTargetChargePercent:
        if delta > 0:
            excessWatts = excessWatts + delta
        if targetSocAt != -1:
            targetSocAt = forecastTime.hour

onePercentWatts = (batteryCapacity / 100)
minuteChargeRate = batteryChargeRate / 60

if maximumSoc < batteryTargetChargePercent:
    toTargetSocMinutes = ((batteryTargetChargePercent - maximumSoc) * onePercentWatts) / minuteChargeRate
            
if minimumSoc < batteryMinChargePercent:
    # Must add some charge to the battery to ensure we don't go down too low
    logger.info("Until next calculation time, lowest battery (%s)%% breaches minimum (%s)%%", minimumSoc, batteryMinChargePercent)
    additionalChargeSoc = batteryMinChargePercent - minimumSoc
    additionalChargeWatts = additionalChargeSoc * onePercentWatts
    minutesToCharge = additionalChargeWatts / minuteChargeRate
    # While charging the battery won't be discharging, so remove the load for this period
    baseLoadWattMinutes = houseBaseload / 60
    unloadedWatts = baseLoadWattMinutes * minutesToCharge
    unloadedSoc = unloadedWatts / onePercentWatts
    
    #logger.info("minimumSoc %s", minimumSoc)
    #logger.info("onePercentWatts %s", onePercentWatts)
    #logger.info("minuteChargeRate %s", minuteChargeRate)
    #logger.info("additionalChargeSoc %s", additionalChargeSoc)
    #logger.info("additionalChargeWatts %s", additionalChargeWatts)
    #logger.info("minutesToCharge %s", minutesToCharge)
    #logger.info("unloadedWatts %s", unloadedWatts)
    
    # Recalculate with unloadedSoc added back to the minimumSoc
    recalcMinimumSoc = minimumSoc + unloadedSoc
    #logger.info("recalcMinimumSoc %s", recalcMinimumSoc)
    recalcAdditionalChargeSoc = batteryMinChargePercent - recalcMinimumSoc
    #logger.info("recalcAdditionalChargeSoc %s", recalcAdditionalChargeSoc)
    
    # If recalc is negative, no recharge would be required if we performed a recharge (ironically)
    if recalcAdditionalChargeSoc < 0:
        unrequiredChargeWatts = abs(recalcAdditionalChargeSoc) * onePercentWatts
        #logger.info("unrequiredChargeWatts %s", unrequiredChargeWatts)
        minutesOffLoad = unrequiredChargeWatts / baseLoadWattMinutes
        #logger.info("minutesOffLoad %s", minutesOffLoad)
        recalcAdditionalChargeWatts = (recalcAdditionalChargeSoc * onePercentWatts) - unrequiredChargeWatts
    else:
        recalcAdditionalChargeWatts = recalcAdditionalChargeSoc * onePercentWatts
 
    recalcMinutesToCharge = recalcAdditionalChargeWatts / minuteChargeRate
    
    #logger.info("recalcAdditionalChargeWatts %s", recalcAdditionalChargeWatts)
    #logger.info("recalcMinutesToCharge %s", recalcMinutesToCharge)
    
    attributes = {}
    attributes['required_soc_extra'] = recalcAdditionalChargeSoc
    attributes['calculated_date'] = now
    attributes['minimum_soc_no_charge'] = round(minimumSoc)
    attributes['maximum_soc'] = round(maximumSoc)
    attributes['target_battery_hour'] = targetSocAt
    attributes['mins_for_target'] = round(toTargetSocMinutes)
    attributes['excess_solar'] = excessWatts
    
    hass.states.set('sensor.battery_charge_required_minutes', recalcMinutesToCharge, attributes)
else:
    logger.info("Lowest battery (%s)%% in excess of minimum (%s)%% - No charge required", minimumSoc, batteryMinChargePercent)
    
    attributes = {}
    attributes['required_soc_extra'] = 0
    attributes['calculated_date'] = now
    attributes['minimum_soc_no_charge'] = round(minimumSoc)
    attributes['maximum_soc'] = round(maximumSoc)
    attributes['target_battery_hour'] = targetSocAt
    attributes['mins_for_target'] = round(toTargetSocMinutes)
    attributes['excess_solar'] = excessWatts
    
    hass.states.set('sensor.battery_charge_required_minutes', 0, attributes)
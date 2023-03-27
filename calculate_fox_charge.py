batteryTargetChargePercent = int(data.get("targetSoc", 100))
batteryCapacity = int(data.get("batteryCapacity", 10400))
batteryChargeRate = int(data.get("batteryChargeRate", 2367))
batteryMinChargePercent = int(data.get("batteryMinChargePercent", 20))
gridSupplyMinSoC = 20 # Battery protected below SoC
houseBaseload = int(data.get("houseBaseload", 350))
cheapRateElectricityStart = data.get("cheapRateElectricityStart", "00:30")
cheapRateElectricityEnd = data.get("cheapRateElectricityEnd", "04:30")

# If the current time is after cheapRateElectricityEnd then terminate the script
now = datetime.datetime.now()

cheapRateElectricityStartParts = cheapRateElectricityStart.split(":")
cheapRateElectricityEndParts = cheapRateElectricityEnd.split(":")

cheapRateElectricityStartHour = int(cheapRateElectricityStartParts[0])
cheapRateElectricityStartMinute = int(cheapRateElectricityStartParts[1])
cheapRateElectricityEndHour = int(cheapRateElectricityEndParts[0])
cheapRateElectricityEndMinute = int(cheapRateElectricityEndParts[1])

cheapRateElectricityStartMinutesOfDay = (cheapRateElectricityStartHour * 60) + cheapRateElectricityStartMinute
cheapRateElectricityEndMinutesOfDay = (cheapRateElectricityEndHour * 60) + cheapRateElectricityEndMinute

lengthOfCheapRatePeriod = cheapRateElectricityEndMinutesOfDay - cheapRateElectricityStartMinutesOfDay

stateOfChargeEntity = data.get("stateOfChargeEntity", "sensor.battery_soc")

solarForecastEntity = data.get("solarForecastEntity", "sensor.solcast_forecast_today") # Valid if run right after Midnight, otherwise will need to be forecast_tomorrow
#solarForecastEntity = data.get("solarForecastEntity", "sensor.solcast_forecast_tomorrow")

solarForecastData = hass.states.get(solarForecastEntity).attributes.get("forecast")
batteryCurrentSoc = int(hass.states.get(stateOfChargeEntity).state)

# Calculate the maximum the battery can be drained from its current state.
batteryMaxDrain = batteryCurrentSoc - batteryMinChargePercent

# From now in the forecasts, work forwards and see if we hit either the min or max (100) soc
# Only care about the first Min/Max event, as that is the only one we can infulence.

onePercentWatts = (batteryCapacity / 100)
minuteChargeRate = batteryChargeRate / 60

timeNow = now.time()
currentHour = timeNow.hour
currentMinute = timeNow.minute

# Hacks for TESTING
# currentHour = 0
# currentMinute = 0
# batteryCurrentSoc = 24

ncSoc = batteryCurrentSoc
ncMin = batteryCurrentSoc
ncMax = batteryCurrentSoc
pSoc = batteryCurrentSoc
pMin = batteryCurrentSoc
pMax = batteryCurrentSoc
cSoc = batteryCurrentSoc
cMin = batteryCurrentSoc
cMax = batteryCurrentSoc

ncTargetAt = -1
pTargetAt = -1
cTargetAt = -1

minimumRequiredChargeSoC = 0
finalTimeForMinCharge = 0

debug = {}
debug2 = {}

for forecastEntry in solarForecastData:
    
    forecastTime = forecastEntry["period_start"].time()    # '2022-11-20T00:00:00+00:00' -> '00:00:00+00:00'
    percentLeftOfHour = 0.0
    
    if currentHour < forecastTime.hour + 1:
        percentLeftOfHour = 1.0
        
    if currentHour == forecastTime.hour:
        if currentMinute == 0:
            percentLeftOfHour = 1.0
        else:
            percentLeftOfHour = 1 - ((100 / (60 / currentMinute)) / 100)
    
    forecastWatts = float(forecastEntry["pv_estimate"]) * 1000    
    
    delta = (forecastWatts * percentLeftOfHour) - (houseBaseload * percentLeftOfHour)
    deltaSoc = (100 / batteryCapacity) * delta
    
    # Calculate moving values
    ncSoc = ncSoc + deltaSoc
    pSoc = pSoc + deltaSoc
    
    # Apply SoC protection
    if pSoc <= gridSupplyMinSoC:
        pSoc = gridSupplyMinSoC
    
    # Calculate Min Max
    if ncSoc < ncMin:
        ncMin = ncSoc
        
    if ncSoc > ncMax:
        ncMax = ncSoc
        
    if pSoc < pMin:
        pMin = pSoc
        
    if pSoc > pMax:
        pMax = pSoc
        
    # Check if target met
    if ncSoc >= batteryTargetChargePercent:
        if ncTargetAt == -1:
            ncTargetAt = forecastTime.hour
            
    if ncSoc >= 100:
        ncSoc = 100
            
    if pSoc >= batteryTargetChargePercent:
        if pTargetAt == -1:
            pTargetAt = forecastTime.hour
            
    if pSoc >= 100:
        pSoc = 100
            
    debug[forecastTime.hour] = "d: " + str(round(deltaSoc)) + ", nc: " + str(round(ncSoc)) + ", p: " + str(pSoc) 

# If the no charge minimum is below the minimum then we must apply a charge
if ncMin < batteryMinChargePercent:
    
    # calculate the minimum amount of SoC that must be added to keep to the min value
    if ncMin < 0:
        minimumRequiredChargeSoC = abs(ncMin) + batteryMinChargePercent
    else:
        minimumRequiredChargeSoC = batteryMinChargePercent - ncMin
        
    timeForMinCharge = (minimumRequiredChargeSoC * onePercentWatts) / minuteChargeRate
    
    # if the time for charge is > charge period, then adjust it down.
    if (lengthOfCheapRatePeriod < timeForMinCharge):
        timeForMinCharge = lengthOfCheapRatePeriod
    
    # While charging, the base load doesn't exist, so the charge time should be less.
    baseloadSocDuringCharge = (timeForMinCharge * (houseBaseload / 60)) / onePercentWatts
    
    adjustedRequiredChargeSoc = minimumRequiredChargeSoC - (baseloadSocDuringCharge * 0.5)
    
    finalTimeForMinCharge = (adjustedRequiredChargeSoc * onePercentWatts) / minuteChargeRate

    chargeStartMinute = cheapRateElectricityStartMinutesOfDay
    chargeEndMinute = chargeStartMinute + finalTimeForMinCharge

    # Run the simulation with a charge included.
    for forecastEntry in solarForecastData:
    
        forecastTime = forecastEntry["period_start"].time()    # '2022-11-20T00:00:00+00:00' -> '00:00:00+00:00'
        
        forecastStartMinutesOfDay = forecastTime.hour * 60
        forecastEndMinutesOfDay = forecastStartMinutesOfDay + 60
        
        percentLeftOfHour = 0.0
    
        if currentHour < forecastTime.hour + 1:
            percentLeftOfHour = 1.0
        
        if currentHour == forecastTime.hour:
            # how much the baseload needs to be adjusted by.
            if currentMinute == 0:
                percentLeftOfHour = 1
            else:
                percentLeftOfHour = 1 - ((100 / (60 / currentMinute)) / 100)
    
        forecastWatts = float(forecastEntry["pv_estimate"]) * 1000    
    
        isCharging = False
        minutesOfHourCharging = -1
        
        # Work out if now is the charge period
        if chargeStartMinute <= forecastStartMinutesOfDay and forecastEndMinutesOfDay >= chargeStartMinute:
            # Started already, finishes some time after (entire hour charging)
            isCharging = True
        
        if chargeStartMinute >= forecastStartMinutesOfDay and forecastEndMinutesOfDay > chargeStartMinute:
            # Starts this hour
            isCharging = True
            minutesOfHourCharging = 60 - (chargeStartMinute - forecastStartMinutesOfDay)
        
        if isCharging and minutesOfHourCharging == -1:
            # Possibly charging for the entire hour
            minutesOfHourCharging = 60
            
        if chargeEndMinute < forecastEndMinutesOfDay and isCharging:
            # ends charging this hour
            minutesOfHourCharging = minutesOfHourCharging - (forecastEndMinutesOfDay - chargeEndMinute)
        
        if chargeEndMinute <= forecastStartMinutesOfDay:
            isCharging = False
            minutesOfHourCharging = 0
        
        percentOfHourCharging = ((100 / 60) * minutesOfHourCharging) / 100
        percentOfHourNotCharging = 1 - percentOfHourCharging
        
        if isCharging:
            delta = (forecastWatts * percentLeftOfHour) + (batteryChargeRate * percentOfHourCharging) - (percentOfHourNotCharging * houseBaseload)
        else:
            delta = (forecastWatts * percentLeftOfHour) - (houseBaseload * percentLeftOfHour)
        
        deltaSoc = (100 / batteryCapacity) * delta

        cSoc = cSoc + deltaSoc
        
        if cSoc < cMin:
            cMin = cSoc
        
        if cSoc > cMax:
            cMax = cSoc

        # Check if target met (only if not charging)
        if cSoc >= batteryTargetChargePercent and !isCharging:
            if cTargetAt == -1:
                cTargetAt = forecastTime.hour
                
        if cSoc >= 100:
            cSoc = 100

        debug2[forecastTime.hour] = "d: " + str(deltaSoc) + ", c: " + str(cSoc) + ", cMin: " + str(round(cMin)) + ", cMax: " + str(round(cMax)) + ", BLSoc: " + str(baseloadSocDuringCharge)

minutesForTarget = ((batteryTargetChargePercent - cMax) * onePercentWatts) / minuteChargeRate

if minutesForTarget < 0:
    minutesForTarget = 0;

attributes = {}
attributes['required_soc_extra'] = round(minimumRequiredChargeSoC)
attributes['calculated_date'] = now
attributes['minimum_soc_no_charge'] = round(pMin)
attributes['maximum_soc_no_charge'] = round(pMax)
attributes['target_battery_hour_no_charge'] = pTargetAt
attributes['target_battery_hour_with_charge'] = cTargetAt
attributes['mins_for_target'] = round(finalTimeForMinCharge + minutesForTarget)

# Debugging attributes
#attributes['time_for_min_charge'] = round(timeForMinCharge)
#attributes['start_at'] = chargeStartMinute
#attributes['end_at'] = chargeEndMinute
#attributes['debug'] = debug
#attributes['debug2'] = debug2

hass.states.set('sensor.battery_charge_required_minutes', round(finalTimeForMinCharge), attributes)

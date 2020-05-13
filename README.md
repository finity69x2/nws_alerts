# nws_alerts
An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component


## Installation:

Clone the Repository and copy the "nws_alerts" directory to your custom_components fold in your config directory

```<config directory>/custom_components/nws_alerts/...```
  
You will end up with two files in that directory - ```"sensor.py"``` and ```"__init__.py"```.


## Configuration:

You can find your Zone or County ID by going to https://alerts.weather.gov/, scroll down to your state and click on the “zone list” and/or "county list" then look for the entry for your county.

To create a sensor instance add the following configuration to your sensor definitions using the zone_id found above:

```
- platform: nws_alerts
  zone_id: 'PAC049'
```

or enter comma separated values for multiple zones:

```
- platform: nws_alerts
  zone_id: 'PAC049,WVC031'
```

After you restart Home Assistant then you should have a new sensor called "sensor.nws_alerts" in your system.

You can overide the sensor default name ("sensor.nws_alerts") to one of your choosing by setting the "name:" option:

```
- platform: nws_alerts
  zone_id: 'INZ009,INC033'
  name: My NWS Alerts Sensor
```

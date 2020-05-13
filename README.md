# nws_alerts
An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component


## Installation:

Clone the Repository and copy the "nws_alerts" directory to your custom_components fold in your config directory

<config directory>/custom_components/nws_alerts/...
  
You will end up with two files in that directory - "sensor.py" and ```"__init__.py"```.


## Configuration:

To create a sensor instance add to your sensor definitions:

```
- platform: nws_alerts
  zone_id: 'PAC049'
```

or comma separated valuesfor multiple zones:

```
- platform: nws_alerts
  zone_id: 'PAC049,WVC031'
```


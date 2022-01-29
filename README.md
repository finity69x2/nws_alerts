# Alerts from the US National Weather Service  (nws_alerts)

An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component

This integration retrieves updated weather alerts every minute from the US NWS API.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created is used in my "NWS Alerts Custom" package - https://github.com/finity69x2/nws_alerts/blob/master/packages/nws_alerts_custom_package.yaml

## Installation:

<b>Manually:</b>

Clone the Repository and copy the "nws_alerts" directory to your "custom_components" directory in your config directory

```<config directory>/custom_components/nws_alerts/...```
  
<b>HACS:</b>

open the HACS section of Home Assistant.

Click the "+ Explore & Add New repositories" button in the bottom right corner.

In the window that opens search for "NWS Alerts".

In the window that opens when you select it click om "Install This Repository in HACS"

After installing the integration you can then configure it using the instructions in the following section.
  
## Configuration:

You can find your Zone or County ID by going to https://alerts.weather.gov/, scroll down to your state and click on the “zone list” and/or "county list" then look for the entry for your county.

There are two ways to configure this integration.

<b>Manually via an entry in your configuration.yaml file:</b>

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

Using the configuration example above the sensor will then be called "sensor.my_nws_alerts_sensor"

<b>Or you can configure the integration via the "Configuration->Integrations" section of the Home Assistant UI.</b>

Look for the integration labeled "NWS Alerts"


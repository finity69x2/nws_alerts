# Alerts from the US National Weather Service  (nws_alerts)

An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component

This integration retrieves updated weather alerts every minute from the US NWS API (by default but it can be changed in the config options).

You can configure the integration to use your NWS Zone, your precise location via GPS coordinates or you can get dynamic location alerts by configuring the integration to use a device_tracker entity from HA as long as that device tracker provides GPS coordinates.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created is used in my "NWS Alerts" package: https://github.com/finity69x2/nws_alerts/blob/master/packages/nws_alerts_package.yaml

You can also display the generated alerts in your frontend. For example usage see: https://github.com/finity69x2/nws_alerts/blob/master/lovelace/alerts_tab

(note: this frontend example uses a custom card but it's not necessary for it's use in the frontend. it's only an example and how I currently use it in my HA)

## Installation:

<b>Manually:</b>

Clone the Repository and copy the "nws_alerts" directory to your "custom_components" directory in your config directory

```<config directory>/custom_components/nws_alerts/...```
  
<b>HACS:</b>

open the HACS section of Home Assistant.

Click the "+ Explore & Download Repositories" button in the bottom right corner.

In the window that opens search for "NWS Alerts".

In the window that opens when you select it click om "Install This Repository in HACS"

After installing the integration you can then configure it using the instructions in the following section.
  
## Configuration:

There are two ways to configure this integration.

<b>You can configure the integration via the "Configuration->Integrations" section of the Home Assistant UI:</b>

Click on "+ Add Integration" buuton in the bottom right corner.

Search for "NWS Alerts" in the list of integrations and follow the UI prompts to configure the sensor.

You can find your Zone or County ID by going to https://alerts.weather.gov/, scroll down to your state and click on the “zone list” and/or "county list" then look for the entry for your county.

There are a few configuration method options to select from. 

Please see the following link to help you decide which option to use:

https://github.com/finity69x2/nws_alerts/blob/master/lookup_options.md

If you select the "Using a device tracker" option under the "GPS Location" option then HA will use the GPS coordinates provided by that tracker to query for alerts so you should follow the same recommendations for using GPS coordinates when using that option.

<b>Or manually via an entry in your configuration.yaml file:</b>

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

or by entering in specific GPS coordinates:

```
- platform: nws_alerts
  gps_loc: 39.52, -119.81
```

or, finally, by adding a device_tracker entity:

```
- platform: nws_alerts
  tracker: 'device_tracker.your_tracker_entity'
```

After you restart Home Assistant then you should have a new sensor called "sensor.nws_alerts" in your system.

You can overide the sensor default name ("sensor.nws_alerts") to one of your choosing by setting the "name:" option:

```
- platform: nws_alerts
  zone_id: 'INZ009,INC033'
  name: My NWS Alerts Sensor
```

Using the configuration example above the sensor will then be called "sensor.my_nws_alerts_sensor".

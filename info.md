# Alerts from the US National Weather Service  (nws_alerts)

## Breaking Change for V5.0

Modified the format of the list of event_id in the attributes

## Description

An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component

This integration retrieves updated weather alerts every minute from the US NWS API.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created is used in my "NWS Alerts Custom" package - https://github.com/finity69x2/NWS-Alerts-Custom-Package

## Installation:

Clone the Repository and copy the "nws_alerts" directory to your "custom_components" directory in your config directory

```<config directory>/custom_components/nws_alerts/...```
  
## Configuration:

You can find your Zone or County ID by going to https://alerts.weather.gov/, scroll down to your state and click on the “zone list” and/or "county list" then look for the entry for your county.

The intergration is configured via the "Configuration->Integrations" section of the Home Assistant UI.

Look for the integration labeled "NWS Alerts" and follow the on-screen prompts.

Using the configuration example above by default the sensor will then be called "sensor.nws_alerts".

If desired you can modify the sensor name via the UI in the initial configuration or later in the entity configuration dialogue box.

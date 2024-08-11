# Alerts from the US National Weather Service  (nws_alerts)

## BREAKING CHANGES IN V5.0

This is a pretty much complete rewrite of the integration to better organize the data for the alerts. All of the data provided by the older versions is still included but it's laid out very differently and as such none of the associated automations package or dashboard examples will continue to function as there currently are.

There are newly updated code examples in this repo "packages" and "dashboard" folders. I have done extensive testing to ensure that the new updated package examples work as desired but of course I couldn't test every situation.

For further support and actual attribute examples please go to the "official" integration thread on the HA forum. The information about the update starts at post #545:

https://community.home-assistant.io/t/severe-weather-alerts-from-the-us-national-weather-service/71853/545

<s><b>Use at your own risk!</b></s>

That was probably overly fatalistic. I just wanted people to understand that there could be unforseen bugs in the integratoin or more likely the code examples and to be aware of that.

## Description:

An updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component

This integration retrieves updated weather alerts every minute from the US NWS API (by default but it can be changed in the config options).

You can configure the integration to use your NWS Zone, your precise location via GPS coordinates or you can get dynamic location alerts by configuring the integration to use a device_tracker entity from HA as long as that device tracker provides GPS coordinates.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created is used in my "NWS Alerts" package: https://github.com/finity69x2/nws_alerts/blob/master/packages/nws_alerts_package.yaml

You can also display the generated alerts in your frontend. For example usage see: https://github.com/finity69x2/nws_alerts/blob/master/lovelace/alerts_tab

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

<b>NOTE: As of HA versoin 2024.5.x the yaml configuration option is broken. I don't know if it will ever be fixed so the only viable config option is via the UI</b>

<b>You can configure the integration via the "Configuration->Integrations" section of the Home Assistant UI:</b>

Click on "+ Add Integration" buuton in the bottom right corner.

Search for "NWS Alerts" in the list of integrations and follow the UI prompts to configure the sensor.

You can find your Zone or County ID by going to https://alerts.weather.gov/, scroll down to your state and click on the “zone list” and/or "county list" then look for the entry for your county.

There are a few configuration method options to select from. 

Please see the following link to help you decide which option to use:

https://github.com/finity69x2/nws_alerts/blob/master/lookup_options.md

If you select the "Using a device tracker" option under the "GPS Location" option then HA will use the GPS coordinates provided by that tracker to query for alerts so you should follow the same recommendations for using GPS coordinates when using that option.

After you restart Home Assistant then you should have a new sensor (by default) called "sensor.nws_alerts" in your system.

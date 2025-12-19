# Alerts from the US National Weather Service (nws_alerts)

## Description:

This custom integration for Home Assistant was originally sourced from [nws_custom_component by eracknaphobia](https://github.com/eracknaphobia/nws_custom_component).

This integration retrieves updated weather alerts (by default) every minute from the US National Weather Service API. After choosing your lookup method, the update retireval time can be changed.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created is used in my ["NWS Alerts" package](https://github.com/finity69x2/nws_alerts/tree/a31ed70c568f942bb09306ee3580d25ba9811d5a/packages). Use the package appropriate for your version.

You can also display the generated alerts in your frontend. For example usage see [here](https://github.com/finity69x2/nws_alerts/blob/a31ed70c568f942bb09306ee3580d25ba9811d5a/lovelace/alerts_tab.yaml).

## Installation:

### HACS:

[![Open your Home Assistant instance and add this repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=finity69x2&repository=nws_alerts&category=integration)


1. Open HACS from your HomeAssitant.

2. Search for "NWS Alerts".
  
3. Either use the 3 vertical dots at the top and select "Download" OR use the download icon at the bottom right.

### Manually:

Clone the Repository and copy the "nws_alerts" directory to your "custom_components" directory in your config directory:

`<config directory>/custom_components/nws_alerts/...`

  
## Configuration:

**BREAKING CHANGES IN V5.0**

This is a pretty much complete rewrite of the integration to better organize the data for the alerts. All of the data in the older versions is still included. It's just laid out very differently and as such none of the associated automations package or dashboard examples will continue to function as there currently are.

There are newly updated code examples in this repo "packages" and "lovelace" folders. I have done extensive testing to ensure that the new updated package examples work as desired but YMMV.

That was probably overly fatalistic. I just wanted people to understand that there could be unforseen bugs in the integration or more likely the code examples and to be aware of that.


**NOTE:** As of HA version 2024.5.x the YAML configuration option is broken. I don't know if it will ever be fixed.

---

1. Navigate to Settings > Devices & Services.

2. Press the "+ Add Integration" button in the bottom right corner.

3. Search for "NWS Alerts" in the list of integrations and follow the UI prompts to configure the sensor.

---


### There are multiple options to configure this integration. Use [NWS Alert Lookup Options](https://github.com/finity69x2/nws_alerts/blob/master/lookup_options.md) to help you decide which option to use:

**NOTE: For current users utilizing NWS Zones, you'll need to edit/delete/re-add your entity!** Recently, the National Weather Service has deprecated the alerts webpage previously used to reference zones. Ref: [Decommissioning of the Alerts Webpage Effective December 2, 2025](https://www.weather.gov/media/notification/pdf_2025/scn25-73_update_alerts_webpage_termination_aaa.pdf).

1. NWS Zone (This was discovered via [Issue #124, comment by 335iguy](https://github.com/finity69x2/nws_alerts/issues/124#issuecomment-3673080677)):

    1a. [NWS GIS Viewer](https://viewer.weather.noaa.gov). This is an interactive GIS map. When the map loads:
   
    * Find the `Layers` button toward the top right of the browser window. I recommend using the `Clear Layers` button first.

    * Enable `NWS Borders` > `NWS County Borders`

    * Enable `Surface Weather Forecast Zones` > `Public Weather Forecast Zones`
  
   
2. Home Assistant location (whatever is set in HomeAssistant)


3. Via a `device_tracker` entity from HomeAssistant. See below for more information.

      3a. In order for this to work as intended, the `device_tracker` **must** contain GPS coordinates. This means that the newly created entity *will dynamically change* based on the coordinates! Very useful when traveling and/or dynamic notifications when you're about to enter a zone with an active alert.


After you restart Home Assistant then you should have a new sensor (by default) called `sensor.nws_alerts`.

## Testing

If there are currently no active alerts for your location but you want to do testing you can use any manually configured location ID that has an active alert.

To find those locations go to: https://api.weather.gov/alerts/active/count. It will provide a list of all areas with active alerts and how many alerts are active for each area.

You can use the given code(s) in your config to get the alerts for the selected zones in the integration.

## Support

For further support and actual attribute examples please go to the ["official" integration thread](https://community.home-assistant.io/t/severe-weather-alerts-from-the-us-national-weather-service/71853/545) on the HA forum. The information about the update starts at post #545.

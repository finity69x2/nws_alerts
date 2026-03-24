# Alerts from the US National Weather Service (nws_alerts)

## Description:

This is an updated version of the nws_alerts custom integration for Home Assistant originally found at github.com/eracknaphobia/nws_custom_component

This integration retrieves updated weather alerts every minute from the US NWS API (by default but it can be changed in the config options).

You can configure the integration to use your NWS Zone or County ID, your precise location via GPS coordinates or you can get dynamic location alerts by configuring the integration to use a device_tracker entity from HA as long as that device tracker provides GPS coordinates.

The integration presents the number of currently active alerts as the state of the sensor and lists many alert details as a list in the attributes of the sensor.

The sensor that is created can be used in my ["NWS Alerts" package](https://github.com/finity69x2/nws_alerts/tree/a31ed70c568f942bb09306ee3580d25ba9811d5a/packages). Use the package appropriate for your version.

You can also display the generated alerts in your frontend. For example usage see [here](https://github.com/finity69x2/nws_alerts/blob/a31ed70c568f942bb09306ee3580d25ba9811d5a/lovelace/alerts_tab.yaml)

## Installation:

### HACS:

- Open the HACS section of Home Assistant.

- Enter "NWS Alerts" into the search bar.

- Look for "NWS Alerts" in the integrations section.

- Click on the entry and then click the "Download" at the bottom right corner.

### Manually:

- Clone the Repository and copy the "nws_alerts" directory from the downloaded directory into your "custom_components" directory in your config directory.

- ```<config directory>/custom_components/nws_alerts/...```


After installing the integration into Home Assistant either manually or via HACS you can then configure it using the instructions in the following section.
  
## Configuration:

Go to "Settings" > "Devices & Services" and in the "Integrations" tab click on "+Add Integration" in the bottom right corner

Search for "NWS Alerts" in the list of integrations and follow the UI prompts to configure the integration.

*** There are a few configuration method options to select from. Please see the following link to help you decide which option to use: https://github.com/finity69x2/nws_alerts/blob/master/lookup_options.md


### If using use either a Zone or County Code:

1. Zone:

    * Open [NWS GIS Viewer](https://viewer.weather.noaa.gov). This is an interactive GIS map. 
   
    * When the map loads find the 'Layers' button toward the top right of the browser window. I recommend using the 'Clear Layers' button first.

    * Enable 'Reference Layers' -> 'Surface Weather Forecast Zones' -> 'Public Weather Forecast Zones'
	
	* Find your zone ID on the map.
	
	* To use the zone id code you will need to modify it as follows:
	  
	  - The state abbreviation from the zone id followed by 'Z' then the three digit numerical portion of the zone id.
	  - For example if the zone id is IN009 the code you will use is INZ009
	  
2. County:

   * Go to https://www.weather.gov/pimar/FIPSCodes
   
   * Find your state then click on the 'jpg' link in the far right column
   
   * Look in the map to find your county.
   
   * To use the county id code you will need to modify it as follows:
	  
	  - Use the two letter USPS state abbreviation followed by 'C' then the last three digits of the county id.
	  - For example if the county id is 18033 the code you will use is INC033 (18 is the state code for indiana)

### If using either GPS coordinates or a device tracker:

   * If you choose to use the GPS option then the location used by your Home Assistant installation will be entered by default. You can change those GPS coordinates to any that you desire.

   * If you select the "Using a device tracker" option under the "GPS Location" option then HA will use the GPS coordinates provided by that tracker to query for alerts so you should follow the same recommendations for using GPS coordinates when using that option.

After you restart Home Assistant then you should have a new sensor (by default) called "sensor.nws_alerts_alerts" in your system.

## Testing:

If there are currently no active alerts for your location but you want to do testing you can use any manually configured location ID that has an active alert.

To find those locations go to: https://api.weather.gov/alerts/active/count you will see a list of all areas with active alerts and how many alerts are active for each area.

You can use the given code(s) in your config to get the alerts for the selected zones in the integration.

## Additional Information:

In release 6.6 I've added "NWSCode" to the Alert list as an additional way to filter alerts. It may make it easier to filter using the code than needing to search thru text strings as I do now in my example packages.

For a full list of the NWS Even Codes see here:

https://vlab.noaa.gov/web/nws-common-alerting-protocol/cap-documentation#_eventcode_inclusion-16

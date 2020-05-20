import requests
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers import config_validation as cv
from .const import (
    API_ENDPOINT,
    USER_AGENT,
    DEFAULT_ICON,
    DEFAULT_NAME,
    CONF_ZONE_ID,
    ATTRIBUTION,
)

# ---------------------------------------------------------
# API Documentation
# ---------------------------------------------------------
# https://www.weather.gov/documentation/services-web-api
# https://forecast-v3.weather.gov/documentation
# ---------------------------------------------------------

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ZONE_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    """ Configuration from yaml """
    name = config.get(CONF_NAME, DEFAULT_NAME)
    zone_id = config.get(CONF_ZONE_ID)
    async_add_entities([NWSAlertSensor(name, zone_id)], True)


async def async_setup_entry(hass, entry, async_add_entities):
    """ Setup the sensor platform. """
    name = entry.data[CONF_NAME]
    zone_id = entry.data[CONF_ZONE_ID]
    async_add_entities([NWSAlertSensor(name, zone_id)], True)


class NWSAlertSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, zone_id):
        """Initialize the sensor."""
        self._name = name
        self._icon = DEFAULT_ICON
        self._state = 0
        self._event = None
        self._event_id = None
        self._display_desc = None
        self._spoken_desc = None
        self._zone_id = zone_id.replace(' ', '')
        self.update()

    @property
    def unique_id(self):
        """
        Return a unique, Home Assistant friendly identifier for this entity.
        """
        return f"{self._name}_{self._name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state message."""
        attrs = {}

        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        attrs['title'] = self._event
        attrs['event_id'] = self._event_id
        attrs['display_desc'] = self._display_desc
        attrs['spoken_desc'] = self._spoken_desc

        return attrs

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        values = self.get_state()
        self._state = values['state']
        self._event = values['event']
        self._event_id = values['event_id']
        self._display_desc = values['display_desc']
        self._spoken_desc = values['spoken_desc']

    def get_state(self):
        values = {'state': 0,
                  'event': None,
                  'event_id': None,
                  'display_desc': None,
                  'spoken_desc': None
                  }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/ld+json'
                   }

        url = '%s/alerts/active/count' % API_ENDPOINT
        r = requests.get(url, headers=headers)
        _LOGGER.debug("getting state for %s from %s" % (self._zone_id, url))
        if r.status_code == 200:
            if 'zones' in r.json():
                for zone in self._zone_id.split(','):
                    if zone in r.json()['zones']:
                        values = self.get_alerts()
                        break

        return values

    def get_alerts(self):
        values = {'state': 0,
                  'event': None,
                  'event_id': None,
                  'display_desc': None,
                  'spoken_desc': None
                  }

        headers = {'User-Agent': USER_AGENT,
                   'Accept': 'application/geo+json'
                   }
        url = '%s/alerts/active?zone=%s' % (API_ENDPOINT, self._zone_id)
        r = requests.get(url, headers=headers)
        _LOGGER.debug("getting alert for %s from %s" % (self._zone_id, url))
        if r.status_code == 200:
            events = []
            headlines = []
            event_id = ''
            display_desc = ''
            spoken_desc = ''
            features = r.json()['features']
            for alert in features:
                event = alert['properties']['event']
                if 'NWSheadline' in alert['properties']['parameters']:
                    headline = alert['properties']['parameters']['NWSheadline'][0]
                else:
                    headline = event

                id = alert['id']
                description = alert['properties']['description']
                instruction = alert['properties']['instruction']

                if event in events:
                    continue

                events.append(event)
                headlines.append(headline)

                if display_desc != '':
                    display_desc += '\n\n-\n\n'

                display_desc += '%s\n%s\n%s' % (headline, description, instruction)
                
                if event_id != '':
                    event_id += '---'
					
                event_id += id

            if headlines:
                num_headlines = len(headlines)
                i = 0
                for headline in headlines:
                    i += 1
                    if spoken_desc != '':
                        if i == num_headlines:
                            spoken_desc += '\n\n-\n\n'
                        else:
                            spoken_desc += '\n\n-\n\n'

                    spoken_desc += headline

            if len(events) > 0:
                event_str = ''
                for item in events:
                    if event_str != '':
                        event_str += ' - '
                    event_str += item

                values['state'] = len(events)
                values['event'] = event_str
                values['event_id'] = event_id
                values['display_desc'] = display_desc
                values['spoken_desc'] = spoken_desc
                
        if r.status_code != 200:
                values['state'] = "Unknown"
                values['event'] = "Unknown"
                values['event_id'] = "Unknown"
                values['display_desc'] = "Unknown"
                values['spoken_desc'] = "Unknown"          

        return values

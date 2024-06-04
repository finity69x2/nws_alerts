# API
API_ENDPOINT = "https://api.weather.gov"
USER_AGENT = "Home Assistant"

# Config
CONF_TIMEOUT = "timeout"
CONF_INTERVAL = "interval"
CONF_ZONE_ID = "zone_id"
CONF_GPS_LOC = "gps_loc"
CONF_TRACKER = "tracker"
CONF_SEND_ALERTS = "send_alerts"
CONF_PERSISTENT_NOTIFICATIONS = "display_persistent_notifictions"
CONF_ANNOUNCE_CRITICAL_TYPES = "announce_critical_alert_types"
CONF_ANNOUNCE_CRITICAL_ENTITIES = "announce_critical_entities"
CONF_ANNOUNCE_TYPES = "announce_alert_types"
CONF_ANNOUNCE_ENTITIES = "announce_entities"
CONF_ANNOUNCE_START_TIME = "announce_alert_start_time"
CONF_ANNOUNCE_END_TIME = "announce_alert_end_time"
CONF_SEND_CRITICAL_TYPES = "send_critical_alert_types"
CONF_SEND_CRITICAL_SERVICES = "send_critical_alert_services"
CONF_SEND_TYPES = "send_alert_types"
CONF_SEND_SERVICES = "send_alert_services"
CONF_SEND_START_TIME = "send_alert_start_time"
CONF_SEND_END_TIME = "send_alert_end_time"

# Defaults
DEFAULT_ICON = "mdi:alert"
DEFAULT_NAME = "NWS Alerts"
DEFAULT_INTERVAL = 1
DEFAULT_TIMEOUT = 120
DEFAULT_SEND_ALERTS = False
DEFAULT_PERSISTENT_NOTIFICATIONS = False
DEFAULT_ANNOUNCE_START_TIME = "08:00:00"
DEFAULT_ANNOUNCE_END_TIME = "20:00:00"
DEFAULT_SEND_START_TIME = "08:00:00"
DEFAULT_SEND_END_TIME = "20:00:00"

NWS_EVENT = "event"
NWS_URL = "url"
NWS_EVENT_ID = "event_id"
NWS_MESSAGE_TYPE = "message_type"
NWS_EVENT_STATUS = "event_status"
NWS_EVENT_SEVERITY = "event_severity"
NWS_EVENT_EXPIRES = "event_expires"
NWS_DISPLAY_DESC = "display_desc"
NWS_CERTAINTY = "certainty"
NWS_DESCRIPTION = "description"
NWS_HEADLINE = "spoken_desc"
NWS_HEADLINE_LONG = "headline_long"
NWS_INSTRUCTION = "instruction"
NWS_EVENT_ID_SHORT = "event_id_short"
NWS_PROPERTIES = "properties"
NWS_URL_PREFIX = "https://api.weather.gov/alerts/"
NWS_ID_PREFIX = "urn:oid:2.49.0.1.840.0."

# Misc
ZONE_ID = ""
VERSION = "2.7"
ISSUE_URL = "https://github.com/finity69x2/nws_alert"
DOMAIN = "nws_alerts"
PLATFORM = "sensor"
ATTRIBUTION = "Data provided by Weather.gov"
COORDINATOR = "coordinator"
PLATFORMS = ["sensor"]

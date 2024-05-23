"""Constants for tests."""

CONFIG_DATA = {"name": "NWS Alerts", "zone_id": "AZZ540,AZC013"}
CONFIG_DATA_2 = {"name": "NWS Alerts YAML", "zone_id": "AZZ540"}
CONFIG_DATA_3 = {"name": "NWS Alerts", "gps_loc": "123,-456"}
CONFIG_DATA_BAD = {"name": "NWS Alerts"}

NWS_COUNT_RESPONSE = {"zones": {"AZZ540": 2, "AZC013": 0}}

NWS_RESPONSE = {
    "@context": [
        "https://geojson.org/geojson-ld/geojson-context.jsonld",
        {
            "@version": "1.1",
            "wx": "https://api.weather.gov/ontology#",
            "@vocab": "https://api.weather.gov/ontology#",
        },
    ],
    "type": "FeatureCollection",
    "features": [
        {
            "id": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.f8c2bb518263d1d5123b3248bf95d57331ebf147.001.1",
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-97.73, 30.89],
                        [-97.62, 30.87],
                        [-97.31, 30.75],
                        [-97.39, 30.63],
                        [-97.51, 30.5],
                        [-97.69000000000001, 30.34],
                        [-97.87000000000002, 30.35],
                        [-98.00000000000001, 30.42],
                        [-97.93000000000002, 30.610000000000003],
                        [-97.73, 30.89],
                    ]
                ],
            },
            "properties": {
                "@id": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.f8c2bb518263d1d5123b3248bf95d57331ebf147.001.1",
                "@type": "wx:Alert",
                "id": "urn:oid:2.49.0.1.840.0.f8c2bb518263d1d5123b3248bf95d57331ebf147.001.1",
                "areaDesc": "Travis, TX; Williamson, TX",
                "geocode": {
                    "SAME": ["048453", "048491"],
                    "UGC": ["TXC453", "TXC491"],
                },
                "affectedZones": [
                    "https://api.weather.gov/zones/county/TXC453",
                    "https://api.weather.gov/zones/county/TXC491",
                ],
                "references": [],
                "sent": "2024-04-28T14:00:00-05:00",
                "effective": "2024-04-28T14:00:00-05:00",
                "onset": "2024-04-28T14:00:00-05:00",
                "expires": "2024-04-28T17:00:00-05:00",
                "ends": "2024-04-28T17:00:00-05:00",
                "status": "Actual",
                "messageType": "Alert",
                "category": "Met",
                "severity": "Minor",
                "certainty": "Likely",
                "urgency": "Expected",
                "event": "Flood Advisory",
                "sender": "w-nws.webmaster@noaa.gov",
                "senderName": "NWS Austin/San Antonio TX",
                "headline": "Flood Advisory issued April 28 at 2:00PM CDT until April 28 at 5:00PM CDT by NWS Austin/San Antonio TX",
                "description": "* WHAT...Urban and small stream flooding caused by excessive\nrainfall is expected.",
                "instruction": "Turn around, don't drown when encountering flooded roads. Most flood\ndeaths occur in vehicles.",
                "response": "Avoid",
                "parameters": {
                    "AWIPSidentifier": ["FLSEWX"],
                    "WMOidentifier": ["WGUS84 KEWX 281900"],
                    "NWSheadline": [
                        "FLOOD ADVISORY IN EFFECT UNTIL 5 PM CDT THIS AFTERNOON"
                    ],
                    "BLOCKCHANNEL": ["EAS", "NWEM", "CMAS"],
                    "VTEC": [
                        "/O.NEW.KEWX.FA.Y.0036.240428T1900Z-240428T2200Z/"
                    ],
                    "eventEndingTime": ["2024-04-28T22:00:00+00:00"],
                },
            },
        },
        {
            "id": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.84378ece4d14118d62d5eb0387b031aef7e5f77d.001.1",
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-97.62, 30.87],
                        [-97.27000000000001, 30.740000000000002],
                        [-97.70000000000002, 30.55],
                        [-97.91000000000001, 30.63],
                        [-97.70000000000002, 30.89],
                        [-97.62, 30.87],
                    ]
                ],
            },
            "properties": {
                "@id": "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.84378ece4d14118d62d5eb0387b031aef7e5f77d.001.1",
                "@type": "wx:Alert",
                "id": "urn:oid:2.49.0.1.840.0.84378ece4d14118d62d5eb0387b031aef7e5f77d.001.1",
                "areaDesc": "Williamson",
                "geocode": {"SAME": ["048491"], "UGC": ["TXZ173"]},
                "affectedZones": [
                    "https://api.weather.gov/zones/forecast/TXZ173"
                ],
                "references": [],
                "sent": "2024-04-28T13:31:00-05:00",
                "effective": "2024-04-28T13:31:00-05:00",
                "onset": "2024-04-28T13:31:00-05:00",
                "expires": "2024-04-28T14:15:00-05:00",
                "ends": None,
                "status": "Actual",
                "messageType": "Alert",
                "category": "Met",
                "severity": "Moderate",
                "certainty": "Observed",
                "urgency": "Expected",
                "event": "Special Weather Statement",
                "sender": "w-nws.webmaster@noaa.gov",
                "senderName": "NWS Austin/San Antonio TX",
                "headline": "Special Weather Statement issued April 28 at 1:31PM CDT by NWS Austin/San Antonio TX",
                "description": "At 131 PM CDT, Doppler radar was tracking a strong thunderstorm near places.",
                "instruction": "If outdoors, consider seeking shelter inside a building.",
                "response": "Execute",
                "parameters": {
                    "AWIPSidentifier": ["SPSEWX"],
                    "WMOidentifier": ["WWUS84 KEWX 281831"],
                    "NWSheadline": [
                        "A strong thunderstorm will impact portions of central Williamson County through 215 PM CDT"
                    ],
                    "eventMotionDescription": [
                        "2024-04-28T18:31:00-00:00...storm...223DEG...20KT...30.66,-97.78"
                    ],
                    "maxWindGust": ["50 MPH"],
                    "maxHailSize": ["0.75"],
                    "BLOCKCHANNEL": ["EAS", "NWEM", "CMAS"],
                    "EAS-ORG": ["WXR"],
                },
            },
        },
    ],
    "title": "Current watches, warnings, and advisories for 30.836 N, 97.592 W",
    "updated": "2024-04-28T19:00:49+00:00",
}

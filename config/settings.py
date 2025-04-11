# Default OSRM API settings
DEFAULT_OSRM_API_SETTINGS = {
    "ACCESS_TOKEN": "",  # Will be provided by user
    "BASE_URL": "https://mapbox-osrm-proxy.d.gcdev.swatrider.com/tdroute/v1/",
    "PROFILES": {
        "truck_staticth": "truck_staticth",
        "lotus_thtruckexp": "lotus_thtruckexp"
    }
}

# Default settings for OSRM validation
DEFAULT_SETTINGS = {
    "BATCH_SIZE": 200,
    "MAX_WORKERS": 7,
    "REQUEST_DELAY": 0.1,
    "MAX_RETRIES": 3,
    "BASE_DELAY": 2,
    "JITTER": 0.5,
    "THRESHOLD": 50
}

# Required columns for store-DC mapping
REQUIRED_COLUMNS = [
    "store_location", 
    "store_number", 
    "dc_location", 
    "dc_code", 
    "origin_lon", 
    "origin_lat", 
    "dest_lon", 
    "dest_lat"
]

# Session state keys
SESSION_KEYS = {
    "PREPARED_DATA": "prepared_data",
    "VALIDATION_RESULTS": "validation_results",
    "VALIDATION_STATS": "validation_stats",
    "PROBLEMATIC_ROUTES": "problematic_routes",
    "OSRM_API_SETTINGS": "osrm_api_settings"
}
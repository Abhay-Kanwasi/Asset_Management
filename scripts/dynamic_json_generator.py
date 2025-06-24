from datetime import datetime, timedelta
import json

# Current UTC time
now = datetime.utcnow()

# Asset definitions
assets = [
    {
        "name": "Asset Due Soon",
        "description": "Asset needing service in 10 minutes",
        "service_time": (now + timedelta(minutes=10)).isoformat() + "Z",
        "expiration_time": (now + timedelta(days=1)).isoformat() + "Z",
        "is_serviced": False
    },
    {
        "name": "Overdue Asset",
        "description": "Asset that missed service time",
        "service_time": (now - timedelta(hours=2)).isoformat() + "Z",
        "expiration_time": (now + timedelta(days=1)).isoformat() + "Z",
        "is_serviced": False
    },
    {
        "name": "Expired Asset",
        "description": "Asset that has expired",
        "service_time": (now - timedelta(hours=2)).isoformat() + "Z",
        "expiration_time": (now - timedelta(hours=1)).isoformat() + "Z",
        "is_serviced": False
    }
]

# Pretty print the JSON
print(json.dumps(assets, indent=2))

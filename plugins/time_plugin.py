from datetime import datetime
import pytz

def run():
    """Get current time information in various formats and timezones"""
    now = datetime.now()
    utc_now = datetime.now(pytz.UTC)
    
    time_data = {
        "current_time": {
            "local": now.strftime("%Y-%m-%d %H:%M:%S"),
            "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": int(now.timestamp()),
            "timezone": str(now.astimezone().tzinfo),
        },
        "formats": {
            "date_only": now.strftime("%Y-%m-%d"),
            "time_only": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "month": now.strftime("%B"),
        }
    }
    
    return time_data 
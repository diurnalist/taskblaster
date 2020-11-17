from datetime import datetime
from pytz import timezone

MY_TIMEZOME = 'America/Chicago'

def start_of_today():
    return (datetime.now(timezone(MY_TIMEZOME))
        .replace(hour=0, minute=0, second=0, microsecond=0))

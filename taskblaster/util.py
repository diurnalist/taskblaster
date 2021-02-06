from datetime import datetime, timedelta
from dateutil.tz import gettz

MY_TIMEZOME = 'America/Chicago'


def start_of_today():
    return (datetime.now(tz=gettz(MY_TIMEZOME))
        .replace(hour=0, minute=0, second=0, microsecond=0))


def one_week_ago():
    return start_of_today() - timedelta(days=7)

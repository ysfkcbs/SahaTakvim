from datetime import date, timedelta


def week_start_for(day: date):
    return day - timedelta(days=day.weekday())


def business_hours(open_hour=17, close_hour=2):
    hours = []
    h = open_hour
    while True:
        hours.append(h)
        if h == close_hour:
            break
        h = (h + 1) % 24
    return hours


def hour_label(hour):
    return f"{hour:02d}:00"

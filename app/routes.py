from datetime import date, datetime, timedelta
from icalendar import Calendar, Event
from flask import Blueprint, Response, request, abort
from zoneinfo import ZoneInfo
from requests import RequestException

from .auth import *
from .logic import get_user, create_user, user_exists
from .models import User

bp = Blueprint("routes", __name__)

@bp.route("/token", methods=['GET'])
def get_token():
    creds = request.json
    username = creds["username"]
    password = creds["password"]

    if user := user_exists(username):
        return user.create_token(password)

    new_user = create_user(username, password)
    return new_user.create_token(password)


@bp.route("/calendar", methods=['GET'])
def calendar_feed():
    def create_detail(template, **values):
        for value in values.values():
            if not value: return ""

        return template.format(**values)

    token = request.args.get("token", "")
    user = get_user(token)
    if user is None:
        abort(401, "Invalid Credentials")

    jobs = user.get_jobs()

    cal = Calendar()
    cal.add("prodid", "-//HS Staff Calendar//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "High Society")

    for job in jobs:
        event = Event()

        event_date = job.get("EventDate")
        start_time = job.get("StartTime")
        end_time = job.get("EndTime")
        hour_length = 0

        if not (start_time and end_time):
            start_date = end_date = date.fromisoformat(event_date[:10])

        else:
            base_date = datetime.fromisoformat(event_date).date()
            start_time = datetime.fromisoformat(start_time).time()
            end_time = datetime.fromisoformat(end_time).time()

            start_date = datetime.combine(base_date, start_time)
            end_date = datetime.combine(base_date, end_time)

            if end_date < start_date:
                end_date += timedelta(days=1)

            start_date = start_date.replace(tzinfo=ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))
            end_date = end_date.replace(tzinfo=ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))

            hour_length = (end_date - start_date).total_seconds() / 3600

        details = ""

        details += create_detail("Role: {job_type}\n\n", job_type=job.get("JobType"))

        if hour_length > 0:
            rate = float(job.get("StaffRate"))
            pay = calculate_pay(rate, hour_length)
            details += f"Pay: {round(hour_length, 1)}h x £{rate:.2f} = £{pay:.2f}\n\n"

        details += create_detail("Uniform: {uniform}\n\n", uniform=job.get("JobsUniforms"))

        details += create_detail("Staffed Booked: {booked}/{required}\n\n", booked=job.get("StaffBooked"), required=job.get("StaffRequired"))

        event.add("summary", job.get("Client", ""))
        event.add("location", job.get("Venue", ""))
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("dtstamp", datetime.now())
        event.add("description", details)
        event.add("url", job.get("MapLink", ""))
        event.add("uid", job.get("EventID", ""))

        cal.add_component(event)

    return Response(cal.to_ical(), mimetype="text/calendar")

@bp.route("/pay", methods=['GET'])
def month_pay():
    token = request.args.get("token", "")

    pay_month = datetime.today() - timedelta(days=12)
    date_str = pay_month.strftime('%Y-%m-01')

    jobs = get_jobs(token, from_date=date_str)

    total_pay = 0

    for job in jobs:
        event_date = job.get("EventDate")
        start_time = job.get("StartTime")
        end_time = job.get("EndTime")
        hour_length = 0

        if start_time and end_time:
            base_date = datetime.fromisoformat(event_date).date()
            start_time = datetime.fromisoformat(start_time).time()
            end_time = datetime.fromisoformat(end_time).time()

            start_date = datetime.combine(base_date, start_time)
            end_date = datetime.combine(base_date, end_time)

            if end_date < start_date:
                end_date += timedelta(days=1)

            start_date = start_date.replace(tzinfo=ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))
            end_date = end_date.replace(tzinfo=ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))

            hour_length = (end_date - start_date).total_seconds() / 3600

        if hour_length > 0:
            rate = float(job.get("StaffRate"))
            pay = calculate_pay(rate, hour_length)

            total_pay += pay

    return {"pay": total_pay, "formatted": f"{total_pay:.2f}"}

@bp.route("/raw", methods=['GET'])
def raw_job_data():
    token = request.args.get("token", "")
    return get_jobs(token)

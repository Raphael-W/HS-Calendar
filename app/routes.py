from datetime import date, datetime, timedelta
from icalendar import Calendar, Event
from flask import Blueprint, Response, request, abort, render_template
from zoneinfo import ZoneInfo

from .auth import *
from .logic import get_user, create_user, user_exists, parse_job_period, build_description, build_pay_day
from .extensions import limiter

bp = Blueprint("routes", __name__)

@bp.route("/", methods=['GET'])
@limiter.exempt
def index():
    return render_template("index.html")

@bp.route("/token", methods=['POST'])
@limiter.limit("10 per 10 minutes")
def get_token():
    creds = request.get_json(silent=True) or {}
    username = (creds.get("username") or "").strip()
    password = creds.get("password") or ""

    if not (username and password):
        abort(400, description="A username and password are required")

    if user := user_exists(username):
        return user.create_token(password)

    new_user = create_user(username, password)
    return new_user.create_token(password)

@bp.route("/calendar", methods=['GET'])
def calendar_feed():
    token = request.args.get("token", "")
    user = get_user(token)
    if user is None:
        abort(401, "Invalid Credentials")

    jobs = user.get_jobs()

    cal = Calendar()
    cal.add("prodid", "-//HS Staff Calendar//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "High Society")

    month = None
    month_pay = 0
    month_hours = 0

    for job in jobs:
        event = Event()

        start_date, end_date, hour_length = parse_job_period(job)

        rate = float(job.get("StaffRate", 0))
        pay = rate * hour_length

        details = build_description(job, hour_length, rate, pay)

        if (month != start_date.month) and (month is not None):
            pay_day = build_pay_day(date(start_date.year, start_date.month, 1), month_pay, month_hours)
            cal.add_component(pay_day)

            month_hours = month_pay = 0

        month = start_date.month
        month_hours += hour_length
        month_pay += pay

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

@bp.route("/raw", methods=['GET'])
def raw_job_data():
    token = request.args.get("token", "")
    user = get_user(token)
    if user is None:
        abort(401, "Invalid Credentials")

    return user.get_jobs()


from .extensions import db
from .auth import authenticate_user, decode_token
from .models import User

from flask import abort
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from icalendar import Event

# === Helpers ===
def s(count):
    if count > 1:
        return "s"
    return ""

# === Users ===
def create_user(username, password):
    new_user = User(username=username.lower())
    db.session.add(new_user)
    db.session.flush()

    jwt_token = authenticate_user(username, password)
    new_user.update_jwt(jwt_token)

    return new_user


def get_user(token):
    try:
        decoded_token = decode_token(token)
    except:
        abort(400, "Invalid token")

    user = User.query.filter_by(username=decoded_token["u"]).first()
    if (user is None) or (not user.verify_token(token)):
        return

    if not user.is_jwt_valid():
        jwt_token = authenticate_user(decoded_token["u"], decoded_token["p"])
        user.update_jwt(jwt_token)

    return user

def user_exists(username):
    return User.query.filter_by(username=username).first()


# === Calendar ===
def parse_job_period(job):
    try:
        event_date = job.get("EventDate")
        start_time = job.get("StartTime")
        end_time = job.get("EndTime")

        if event_date is None:
            return None

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
                end_date += timedelta(days = 1)

            start_date = start_date.replace(tzinfo = ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))
            end_date = end_date.replace(tzinfo = ZoneInfo("Europe/London")).astimezone(ZoneInfo("UTC"))

            hour_length = (end_date - start_date).total_seconds() / 3600

        return start_date, end_date, hour_length

    except Exception:
        return None


def create_detail(template, **values):
    for value in values.values():
        if not value: return ""

    return template.format(**values)


def build_description(job, hour_length, rate, pay):
    details = ""

    details += create_detail("Role: {job_type}\n\n", job_type = job.get("JobType"))

    if hour_length > 0:
        details += f"Pay: {round(hour_length, 1)}h x £{rate:.2f} = £{pay:.2f}\n\n"

    details += create_detail("Uniform: {uniform}\n\n", uniform = job.get("JobsUniforms"))

    details += create_detail("Staffed Booked: {booked}/{required}\n\n",
                             booked = job.get("StaffBooked"), required = job.get("StaffRequired"))

    return details

def build_pay_day(month_date, pay, hours, shifts):
    pay_day = Event()

    pay_date_date = month_date.replace(day = 12)
    if (weekday := pay_date_date.weekday()) > 4:
        pay_date_date -= timedelta(days = weekday % 4)

    description = f"Pay: £{pay:.2f} (inc. £{pay * 0.1207:.2f} holiday pay)\n\nHours: {round(hours, 1)}h across {shifts} shift{s(shifts)}\n\n"
    description += "Please note:\nThis is only an approximation and does not include fuel or taxi allowances."

    pay_day.add("summary", "Pay Day!")
    pay_day.add("dtstart", pay_date_date)
    pay_day.add("dtend", pay_date_date)
    pay_day.add("dtstamp", datetime.now())
    pay_day.add("description", description)
    pay_day.add("uid", f"{pay_date_date.month}-{pay_date_date.year}-Pay-Day")

    return pay_day
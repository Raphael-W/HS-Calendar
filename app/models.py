import time
import json

from .extensions import db
from .auth import decode_jwt, decode_token, make_token, make_hs_request, authenticate_user

class User(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String, primary_key=True, nullable=False)
    jwt = db.Column(db.String, nullable=True)
    expiry = db.Column(db.Integer, nullable=True)
    staff_id = db.Column(db.Integer, nullable=True)
    kid = db.Column(db.Integer, nullable=False, default=1, server_default="1")


    def is_jwt_valid(self):
        return self.expiry > time.time()


    def update_jwt(self, jwt):
        decoded_jwt = decode_jwt(jwt)
        self.jwt = jwt
        self.expiry = decoded_jwt["expiry"]

        if self.staff_id is None:
            self.fetch_and_set_staff_id()


    def create_token(self, password):
        token = make_token(self.username, password, self.kid)
        jwt_token = authenticate_user(self.username, password)
        self.update_jwt(jwt_token)
        return token


    def verify_token(self, token):
        username, password, kid = decode_token(token)
        valid_username = username == self.username
        valid_kid = kid == self.kid
        return valid_username and valid_kid


    def fetch_and_set_staff_id(self):
        params = {"username": self.username}
        response = make_hs_request("EMSSecurityUserItems60", self.jwt, params = params)
        self.staff_id = json.loads(response.text)["StaffItem"]


    def get_jobs(self, from_date = "1990-01-01"):
        params = {
            "staffId"  : self.staff_id,
            "eventDate": from_date,
            "history"  : "false",
        }

        response = make_hs_request("BookedJobs65", self.jwt, params = params)
        return response.json()
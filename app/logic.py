from .extensions import db
from .auth import authenticate_user, decode_token
from .models import User

from flask import abort

# === Users ===
def create_user(username, password):
    new_user = User(username=username)
    db.session.add(new_user)
    db.session.flush()

    jwt_token = authenticate_user(username, password)
    new_user.update_jwt(jwt_token)

    db.session.commit()
    return new_user


def get_user(token):
    try:
        username, password, _ = decode_token(token)
    except:
        abort(400, "Invalid token")

    user = User.query.filter_by(username=username).first()
    if (user is None) or (not user.verify_token(token)):
        return

    if not user.is_jwt_valid():
        jwt_token = authenticate_user(username, password)
        user.update_jwt(jwt_token)

    return user

def user_exists(username):
    return User.query.filter_by(username=username).first()

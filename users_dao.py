"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import User

from db import db


def get_user_by_session_token(session_token):
    """
    Returns a user object from the database given a session token
    """
    return User.query.filter(User.session_token == session_token).first()


def get_user_by_update_token(update_token):
    """
    Returns a user object from the database given an update token
    """
    return User.query.filter(User.update_token == update_token).first()


def renew_session(update_token):
    """
    Renews a user's session token
    
    Returns the User object
    """
    user = get_user_by_update_token(update_token)

    if user is None:
        raise Exception("Invalid update token")

    user.renew_session()
    db.session.commit()

    return user

import json 

from db import db
from db import Event
from db import User 
from db import Category
from db import Bucket
from db import Asset

import datetime
import random

from flask import Flask
from flask import request 

import os

from crontab import CronTab
# Third-party libraries
from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# define db filename 

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
db_filename = "bukethaca.db"

# setup config 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# initialize app
db.init_app(app)
with app.app_context():
    db.create_all()

# generalized response formats 
def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code


# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# -- GOOGLE ROUTES ------------------------------------------------------
@app.route("/")
def index():
    """
    Endpoint for Homepage, IDK if we need this tho cause it is not a web app but oh well

    Returns HTML as a string
    """
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    """
    After login route, google asks the user for consent and stuff to share their info with is, Then google generates and sends us 
    a unique code that is sent to the callpack endpoint

    This endpoint gets that code
    """ 
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, 
        name=users_name, 
        email=users_email, 
        profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if User.query.filter_by(id=unique_id).first() is None:
        db.session.add(user)
        db.session.commit()
        return success_response(new_user.serialize(), 201)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    """
    Endpoint for Logging Out
    """
    logout_user()
    return redirect(url_for("index"))


# -- EVENT ROUTES ------------------------------------------------------

@app.route("/api/events/")
def get_all_events():
    """
    CHECKOVER Endpoint for getting all events
    """
    return success_response({"events": [e.serialize() for e in Event.query.order_by(Event).date.desc().all()]})
    
@app.route("/api/events/", methods=["POST"])
def create_event():
    """
    CHECKOVER Endpoint for creating a event
    """
    body = json.loads(request.data)
    title = body.get("title")
    if title is None:
        return failure_response("Please put something for name of event", 400)
    host_name = body.get("host_name")
    if host_name is None:
        return failure_response("Please put something for host name", 400)
    date = body.get("date")
    if date is None:
        return failure_response("Please put something for date", 400) 
    location = body.get("location")
    if location is None:
        return failure_response("Please put something for location", 400) 
    description = body.get("description")
    if description is None:
        return failure_response("Please put something for the description", 400) 
    image_data = body.get("image_data")
    if image_data is None:
            return failure_response("No base64 image passed in!")
    new_event = Event(title=title, host_name=host_name, date=date, location=location, description=description)
    db.session.add(new_event)
    db.session.commit()
    image = Asset(image_data=image_data, event_id=new_event.id)
    db.session.add(image)
    db.session.commit()
    return success_response(new_event.serialize(), 201)

@app.route("/api/events/<int:event_id>/")
def get_specific_event(event_id):
    """
    CHECKOVER Endpoint for getting a event by id 
    """
    event= Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Sorry, event was not found")
    return success_response(event.serialize())

@app.route("/api/events/<int:event_id>/", methods=["DELETE"])
def delete_event(event_id):
    """
    CHECKOVER Endpoint for deleting an event by id
    """
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    db.session.delete(event)
    db.session.commit()
    return success_response(event.serialize())

# -- USER ROUTES ------------------------------------------------------
@app.route("/api/users/", methods=["POST"])
def create_user():
    """
    CHECKOVER Endpoint for creating a user
    """
    body = json.loads(request.data)
    name=body.get("name")
    email=body.get("email")
    if name is None:
        return failure_response("Please enter something for name", 400)
    if email is None:
        return failure_response("Please enter something for email", 400)
    new_user = User(name=name, email=email)
    db.session.add(new_user)
    db.session.commit()
    return success_response(new_user.serialize(), 201)

@app.route("/api/users/<int:user_id>/")
def get_specific_user(user_id):
    """
    CHECKOVER Endpoint for getting user by id 
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())

@app.route("/api/users/<int:user_id>/events/<int:event_id>/bookmark/", methods=["POST"])
def bookmark_event(event_id, user_id):
    """
    CHECKOVER Endpoint for adding an event to user's saved events 
    """
    body = json.loads(request.data)
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    # checks if user exist
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # checks if user is student or instructor 
    if body.get("type") == "event":
        user.saved_events.append(event)
        db.session.commit()
    elif body.get("type") == "bucket":
        user.saved_buckets.append(event)
        db.session.commit()
    else:
        return failure_response("Invalid input.", 400)
    return success_response(user.serialize())

@app.route("/api/category/", methods=["POST"])
def create_category():
    """
    CHECKOVER Endpoint for creating a category
    """
    body = json.loads(request.data)
    description = body.get("description")
    color = body.get("color")
    category = Category(description=description, color=color)
    db.session.add(category)
    db.session.commit()
    return success_response(category.serialize())

### JAC
@app.route("/api/")
def get_random_event():
    list = Event.query.all() + Bucket.query.all()
    random.shuffle(list)
    return success_response(list[0].serialize())

@app.route("/api/")
def get_all_bucket():
    """
    Endpoint for getting all Bucket items
    """
    return success_response({"buckets": [b.serialize() for b in Bucket.query.all()]})
    

@app.route("/api/<int:user_id>/")
def get_all_bookmark_current():
    """
    Endpoint for getting all bookmarked current events
    """
    return success_response(User.serialize_saved_buckets()) 
    

@app.route("/api/")
def get_all_bookmark_bucket():
    """
    Endpoint for getting all bookmarked bucket events
    """
    return success_response(User.serialize_saved_current()) 
    

@app.route("/api/user/<int:user_id>/bookmark/bucket/<int:bucket_id>", methods=["DELETE"])
def delete_bookmark_bucket(user_id, bucket_id):
    """
    Endpoint for deleting saved bucket
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    for bucket in user.saved_buckets:
        if bucket.id==bucket_id:
            user.saved_buckets.delete(bucket)
    db.session.commit()
    return success_response(bucket.simple_serialize(), 200)

@app.route("/api//<int:user_id>/bookmark/event/<int:event_id>", methods=["DELETE"])
def delete_bookmark_current(user_id, event_id):
    """
    Endpoint for deleting saved current event
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    for event in user.saved_events:
        if event.id==event_id:
            user.saved_events.delete(event)
    db.session.commit()
    return success_response(event.simple_serialize(), 200)
    



# -- CATEGORIES ROUTES ------------------------------------------------------
@app.route("/api/events/<int:event_id>/category/<int:category_id>", methods=["POST"])
def assign_category(event_id, category_id):
    """
    CHECKOVER Endpoint for assigning a category to a event by id
    """
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    # process request body if task IS found 
    body = json.loads(request.data)
    name = body.get("name")
    color = body.get("color")
    # create new Category object if it doesn't exist,
    # otherwise assign task to existing category 
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    event.categories.append(category)
    db.session.commit()
    return success_response(event.serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

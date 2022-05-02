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

# define db filename 

app = Flask(__name__)
db_filename = "cms.db"

# setup config 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

# initialize app
db.init_app(app)
with app.app_context():
    db.create_all()

# generalized response formats 
def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code

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
    # return success_response(user.serialize_saved_buckets()) 
    pass
    

@app.route("/api/")
def get_all_bookmark_bucket():
    """
    Endpoint for getting all bookmarked bucket events
    """
    # return success_response(user.serialize_saved_current()) 
    pass

@app.route("/api/user/<int:user_id>/bookmark/bucket/<int:bucket_id>", methods=["DELETE"])
def delete_bookmark_bucket(user_id, bucket_id):
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

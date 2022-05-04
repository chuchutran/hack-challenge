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



# -- USER ROUTES ------------------------------------------------------
@app.route("/api/users/", methods=["POST"])
def create_user():
    """
    Endpoint for creating a user
    """
    body = json.loads(request.data)
    name=body.get("name")
    email=body.get("email")
    phone_number=body.get("phone_number")
    if name is None:
        return failure_response("Please enter something for name", 400)
    if email is None:
        return failure_response("Please enter something for email", 400)
    if phone_number is None:
        return failure_response("Please enter something for phone_number", 400)
    new_user = User(name=name, email=email, phone_number=phone_number)
    db.session.add(new_user)
    db.session.commit()
    return success_response(new_user.serialize(), 201)

@app.route("/api/users/<int:user_id>/")
def get_specific_user(user_id):
    """
    Endpoint for getting user by id 
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())



# -- EVENT ROUTES ------------------------------------------------------
@app.route("/api/events/")
def get_all_events():
    """
    Endpoint for getting all events
    """
    # return success_response({"events": [e.serialize() for e in Event.query.order_by(Event.date.desc())]})
    return success_response({"events": [e.serialize() for e in Event.query.all()]})
    
@app.route("/api/users/<int:user_id>/events/", methods=["POST"])
def create_event(user_id):
    """
    Endpoint for creating a event
    """
    # checks if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

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
    # creates image object 
    image = Asset(image_data=image_data)
    db.session.add(image)
    db.session.commit()
    # creates event object 
    new_event = Event(title=title, host_name=host_name, date=date, location=location, description=description, image_id=image.id)
    db.session.add(new_event)
    # adds event to user created
    user.created_events.append(new_event)
    db.session.commit()
    return success_response(new_event.serialize(), 201)

@app.route("/api/events/<int:event_id>/")
def get_specific_event(event_id):
    """
    Endpoint for getting a event by id 
    """
    # checks if event exists
    event= Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Sorry, event was not found.")
    return success_response(event.serialize())

@app.route("/api/users/<int:user_id>/events/<int:event_id>/", methods=["DELETE"])
def delete_event(user_id,event_id):
    """
    Endpoint for deleting an event by id
    """
    # checks if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    # checks if event exists
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    # checks if user created the event
    if event not in user.created_events:
        return failure_response("User did not create this event!")
    db.session.delete(event)
    db.session.commit()
    return success_response(event.serialize())

@app.route("/api/events/random/")
def get_random_event():
    """
    Endpoint for getting a random event
    """
    list = Event.query.all() + Bucket.query.all()
    random.shuffle(list)
    return success_response(list[0].serialize())

@app.route("/api/users/<int:user_id>/events/bookmark/")
def get_all_bookmark_current(user_id):
    """
    Endpoint for getting all bookmarked current events
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize_saved_events()) 

@app.route("/api/users/<int:user_id>/events/<int:event_id>/bookmark/", methods=["DELETE"])
def delete_bookmark_current(user_id, event_id):
    """
    Endpoint for deleting saved current event
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    for event in user.saved_events:
        if event.id==event_id:
            user.saved_events.remove(event)
    db.session.commit()
    return success_response(event.simple_serialize(), 200)



# -- BUCKET ROUTES ------------------------------------------------------
@app.route("/api/buckets/")
def get_all_bucket():
    """
    Endpoint for getting all Bucket items
    """
    return success_response({"buckets": [b.serialize() for b in Bucket.query.all()]})
    
@app.route("/api/buckets/", methods=["POST"])
def create_bucket():
    """
    Endpoint for creating a bucketlist activity
    """
    body = json.loads(request.data)
    description = body.get("description")
    if description is None:
        return failure_response("Please put something for the description", 400)
    status = body.get("status")
    if status is None:
        return failure_response("Please indicate status of bucketlist activity", 400)
    bucket = Bucket(description=description, status=status)
    db.session.add(bucket)
    db.session.commit()
    return success_response(bucket.serialize(), 201)

@app.route("/api/users/<int:user_id>/buckets/bookmark/")
def get_all_bookmark_bucket(user_id):
    """
    Endpoint for getting all bookmarked bucket events
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize_saved_buckets()) 

@app.route("/api/users/<int:user_id>/buckets/<int:bucket_id>/bookmark/", methods=["DELETE"])
def delete_bookmark_bucket(user_id, bucket_id):
    """
    Endpoint for deleting saved bucket
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    bucket = Bucket.query.filter_by(id=bucket_id).first()
    if bucket is None:
        return failure_response("Bucket not found!")
    for bucket in user.saved_buckets:
        if bucket.id==bucket_id:
            user.saved_buckets.remove(bucket)
    db.session.commit()
    return success_response(bucket.serialize(), 200)

# @app.route("/api/users/<int:user_id>/buckets/<int:bucket_id>/update", methods=["POST"])
# def update_bucket_status(user_id, bucket_id):
#     """
#     Endpoint for updating the status of a bucket list activity
#     """
#     user = User.query.filter_by(id=user_id).first()
#     if user is None:
#         return failure_response("User not found!")
#     bucket = Bucket.query.filter_by(id=bucket_id).first()
#     if bucket is None:
#         return failure_response("Bucket not found!")
#     body = json.loads(request.data)
#     status = body.get("status")
#     if status is None:
#         return failure_response("Please put something for the status", 400)


# -- CATEGORIES ROUTES ------------------------------------------------------
@app.route("/api/category/", methods=["POST"])
def create_category():
    """
    Endpoint for creating a category
    """
    body = json.loads(request.data)
    description = body.get("description")
    if description is None:
        return failure_response("Please put something for the description", 400)
    color = body.get("color")
    if color is None:
        return failure_response("Please indicate color for the category", 400)
    category = Category(description=description, color=color)
    db.session.add(category)
    db.session.commit()
    return success_response(category.serialize())
    
@app.route("/api/category/<int:category_id>/events")
def get_category(category_id):
    """
    Endpoint for getting events by category
    """
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    return success_response(category.serialize())

@app.route("/api/category/<int:category_id>/events/<int:event_id>/assign", methods=["POST"])
def assign_category(event_id, category_id):
    """
    Endpoint for assigning a category to a event by id
    """
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    event.categories.append(category)
    db.session.commit()
    return success_response(event.serialize())

# -- OTHER ROUTES ----------------------------------------------------------
@app.route("/api/users/<int:user_id>/events/<int:occasion_id>/bookmark/", methods=["POST"])
def bookmark_occasion(occasion_id, user_id):
    """ 
    Endpoint for adding an occasion to user's saved events or buckets based on type 
    """
    # checks if user exist
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    body = json.loads(request.data)
    if body.get("type") == "event":
        event = Event.query.filter_by(id=occasion_id).first()
        if event is None:
            return failure_response("Event not found!")
        user.saved_events.append(event)
        db.session.commit()
    elif body.get("type") == "bucket":
        bucket = Bucket.query.filter_by(id=occasion_id).first()
        if bucket is None:
            return failure_response("Bucketlist activity not found!")
        user.saved_buckets.append(bucket)
        db.session.commit()
    else:
        return failure_response("Sorry, something went wrong.", 400)
    return success_response(user.serialize())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

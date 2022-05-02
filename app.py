import json 

from db import db
from db import Event
from db import User 
from db import Category

from flask import Flask
from flask import request 

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
    Endpoint for getting all events
    """
    return success_response({"events": [e.serialize() for e in Event.query.all()]})
    
@app.route("/api/events/", methods=["POST"])
def create_event():
    """
    Endpoint for creating a course
    """
    body = json.loads(request.data)
    name = body.get("name")
    date = body.get("date")
    if date is None:
        return failure_response("Please put something for date", 400) 
    if name is None:
        return failure_response("Please put something for name of event", 400)
    new_event = Event(name=name, date=date)
    db.session.add(new_event)
    db.session.commit()
    return success_response(new_event.serialize(), 201)

@app.route("/api/events/<int:event_id>/")
def get_specific_event(event_id):
    """
    Endpoint for getting a event by id 
    """
    event= Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Sorry, event was not found")
    return success_response(event.serialize())

@app.route("/api/events/<int:event_id>/", methods=["DELETE"])
def delete_event(event_id):
    """
    Endpoint for deleting an event by id
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
    Endpoint for creating a user
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
    Endpoint for getting user by id 
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())

@app.route("/api/events/<int:event_id>/add/", methods=["POST"])
def add_event(event_id, user_id):
    """
    Endpoint for adding an event to user's saved events 
    """
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    # process request body if course IS found 
    body = json.loads(request.data)
    event_id = body.get("event_id")
    type = body.get("type")

    # checks if user exist
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # checks if user is student or instructor 
    if type == "student":
        course.students.append(user)
        db.session.commit()
    elif type == "instructor":
        course.instructors.append(user)
        db.session.commit()
    else:
        return failure_response("Invalid input.", 400)
    return success_response(course.serialize())


# -- CATEGORIES ROUTES ------------------------------------------------------
@app.route("/api/events/<int:event_id>/category/", methods=["POST"])
def assign_category(event_id):
    """
    Endpoint for assigning a category to a event by id
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
    category = Category.query.filter_by(color=color).first()
    if category is None:
        category = Category(name=name, color=color)
    event.categories.append(category)
    db.session.commit()
    return success_response(event.serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

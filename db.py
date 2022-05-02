import code
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

category_association_table = db.Table(
    "association_category",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id")), 
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"))
    )

saved_events_association_table = db.Table(
    "association_saved_events", 
    db.Column("saved_event_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("users_saved_id", db.Integer, db.ForeignKey("events.id"))
    )

saved_buckets_association_table = db.Table(
    "association_saved_buckets",
    db.Column("saved_bucket_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("users_saved_id", db.Integer, db.ForeignKey("buckets.id"))
    )

class User(db.Model):
    """
    User model 

    Many-to-many relationship with Events table
    """

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    saved_events = db.relationship("Event", secondary=saved_events_association_table, back_populates="users_saved")
    saved_buckets = db.relationship("Bucket", secondary=saved_buckets_association_table, back_populates="users_saved")
   
    def _init_(self, **kwargs):
        """
        Initialize Course object/entry
        """
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")
        self.password = kwargs.get("password")


    
class Event(db.Model):
    """
    Event model 

    Many-to-many relationship with Users table
    Many-to-many relationship with Category table
    """

    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    categories = db.relationship("Category", secondary=category_association_table, back_populates="event")
    users_saved = db.relationship("User", secondary=saved_events_association_table, back_populates="saved_events")

    def _init_(self, **kwargs):
        """
        Initialize Course object
        """
        self.name = kwargs.get("name")
        self.date = kwargs.get("date")
        self.categories = kwargs.get("categories")
    
    def serialize(self):
        """
        Serializes Course object
        """
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "categories": [c.simple_serialize() for c in self.assignments], 
            "type": "event"
        }
    
        

class Bucket(db.Model):
    """
    Bucket model 

    Has a many-to-many relationship with Users table
    """

    __tablename__ = "buckets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    users_saved = db.relationship("User", secondary=saved_buckets_association_table, back_populates="saved_buckets")

    def _init_(self, **kwargs):
        """
        Initialize Bucket object
        """
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
    
    def simple_serialize(self):
        """
        Serializes a Bucket object 
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description, 
            "type" = "bucket"
        }

class Category(db.Model):
    """
    Category model

    Has a many-to-many relationship with Events table
    """

    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    color = db.Column(db.String, nullable=False)
    events = db.relationship("Event", secondary=category_association_table, back_populates="categories")
    
    def _init_(self, **kwargs):
        """
        Initialize Category object/entry
        """
        self.name = kwargs.get("name")
        self.color = kwargs.get("color")

    def serialize(self):
        """
        Serializes a Category object 
        """
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "events": [e.serialize() for e in self.events]
        }

    def simple_serialize(self):
        """
        Simple serializes a Category object 
        """
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }

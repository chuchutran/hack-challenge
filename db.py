import code
from flask_sqlalchemy import SQLAlchemy
import base64
import boto3
import datetime
import io
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
from PIL import Image
import random
import re
import string

import hashlib
import bcrypt

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
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    saved_events = db.relationship("Event", secondary=saved_events_association_table, back_populates="users_saved")
    saved_buckets = db.relationship("Bucket", secondary=saved_buckets_association_table, back_populates="users_saved")

    #session
    session_token = db.Column(db.String, nullable=True, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=True)
    update_token = db.Column(db.String, nullable=True, unique=True)
   
    def _init_(self, **kwargs):
        """
        Initialize User object/entry
        """
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))

    def serialize(self):
        """
        Serializes User object
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "saved_events": [e.simple_serialize() for e in self.saved_events], 
            "saved_buckets": [b.simple_serialize() for b in self.saved_buckets]
        }

    def serialize_saved_buckets(self):
        """
        serialize only saved buckets from user
        """
        return{
            "saved_buckets": [b.simple_serialize() for b in self.saved_buckets]
        }
    
    def serialize_saved_current(self):
        """
        serialize only saved buckets from user
        """
        return{
            "saved_current": [e.simple_serialize() for e in self.saved_events]
        }

    
class Event(db.Model):
    """
    Event model 

    Many-to-many relationship with Users table
    Many-to-many relationship with Category table
    One-to-many relationship with Asset table
    """

    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    host_name = db.Column(db.String, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    categories = db.relationship("Category", secondary=category_association_table, back_populates="events")
    users_saved = db.relationship("User", secondary=saved_events_association_table, back_populates="saved_events")

    def _init_(self, **kwargs):
        """
        Initialize Event object
        """
        self.title = kwargs.get("title")
        self.host_name = kwargs.get("host_name")
        self.date = kwargs.get("date")
        self.location = kwargs.get("location")
        self.description = kwargs.get("description")
    
    def serialize(self):
        """
        Serializes Event object
        """
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "location": self.location,
            "description": self.description,
            "categories": [c.simple_serialize() for c in self.categories], 
            "type": "event"
        }

    def simple_serialize(self):
        """
        Simple serializes Event object
        """
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "location": self.location,
            "description": self.description
        }
        

class Bucket(db.Model):
    """
    Bucket model 

    Has a many-to-many relationship with Users table
    """

    __tablename__ = "buckets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String, nullable=True)
    status = db.Column(db.Boolean, default=False)
    users_saved = db.relationship("User", secondary=saved_buckets_association_table, back_populates="saved_buckets")

    def _init_(self, **kwargs):
        """
        Initialize Bucket object
        """
        self.description = kwargs.get("description")
        self.status = kwargs.get("status")
    
    def simple_serialize(self):
        """
        Serializes a Bucket object 
        """
        return {
            "id": self.id,
            "description": self.description, 
            "status": self.status,
            "type": "bucket"
        }

class Category(db.Model):
    """
    Category model

    Has a many-to-many relationship with Events table
    """

    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String, nullable=False)
    color = db.Column(db.String, nullable=False)
    events = db.relationship("Event", secondary=category_association_table, back_populates="categories")

    def _init_(self, **kwargs):
        """
        Initialize Category object/entry
        """
        self.description = kwargs.get("description")
        self.color = kwargs.get("color")

    def serialize(self):
        """
        Serializes a Category object 
        """
        return {
            "id": self.id,
            "description": self.description,
            "color": self.color,
            "events": [e.simple_serialize() for e in self.events]
        }

    def simple_serialize(self):
        """
        Simple serializes a Category object 
        """
        return {
            "id": self.id,
            "description": self.description,
            "color": self.color
        }

# class Token(db.Model):
#     """
#     Token Model

#     one to one relationship with User
#     """



EXTENSIONS = ["png", "gif", "jpg", "jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com" 

class Asset(db.Model):
    """
    Asset Model

    Has a one-to-one relationship with Event table
    """
    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_url = db.Column(db.String, nullable=True)
    salt =  db.Column(db.String, nullable=False)
    extension =  db.Column(db.String, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    def __init__(self,**kwargs):
        """
        Initializes an Asset object/entry
        """
        self.event_id = kwargs.get("event_id")
        self.create(kwargs.get("image_data"))

    def serialize(self):
        """
        Serialize Asset object
        """
        return{
            "url": f"{self.base_url}/{self.salt}.{self.extension}",
            "created_at":str(self.created_at)
        }

    def create(self, image_data):
        """
        Given an image in base64 form, it
        1. Rejects the image is the filetype is not supported
        2. Generates a random string for the image file name
        3. Decodes the image and attempts to upload it to AWS
        """
        try:
            ext = guess_extension(guess_type(image_data)[0])[1:]

            #only accepts supported file types
            if ext not in EXTENSIONS:
                raise Exception(f"Unsupported file type: {ext}")


            #generate random strong name for file
            salt = "".join(
                random.SystemRandom().choice(
                    string.ascii_uppercase+ string.digits
                )
                for _ in range(16)
            )

            #decode the image and upload to aws
            #remove header of base64 string
            img_str = re.sub("^data:image/.+;base64,", "", image_data)
            img_data = base64.b64decode(img_str)
            img = Image.open(BytesIO(img_data))

            self.base_url = S3_BASE_URL
            self.salt = salt
            self.extension = ext
            self.width = img.width
            self.height = img.height
            self.created_at = datetime.datetime.now()

            img_filename = f"{self.salt}.{self.extension}"
            self.upload(img, img_filename)

        except Exception as e:
            print(f"Error when creating image: {e}")

    def upload(self, img, img_filename):
        """
        Attempt to upload the image to the specified S3 bucket
        """
        try:
            #save image temporarily on server
            img_temploc = f"{BASE_DIR}/{img_filename}"
            img.save(img_temploc)
            
            s3_client = boto3.client("s3")
            s3_client.upload_file(img_temploc, S3_BUCKET_NAME, img_filename)

            # make s3 image url is public
            s3_resource = boto3.resource("s3")
            object_acl = s3_resource.ObjectAcl(S3_BUCKET_NAME, img_filename)
            object_acl.put(ACL="public-read")

            os.remove(img_temploc)


        except Exception as e:
            print(f"Error when uploading image: {e}")


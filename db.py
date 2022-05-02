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

'''
IMAGES
'''

EXTENSTIONS = ["png", "gif", "jpg", "jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com" 

class Asset(db.Model):
    '''
    Asset Model
    '''
    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_url = db.Column(db.String, nullable=True)
    salt =  db.Column(db.String, nullable=False)
    extention =  db.Column(db.String, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self,**kwargs):
        '''
        Initializes an Asset object
        '''
        self.create(kwargs.get("image_data"))

    def serialize(self):
        '''
        serialize asset object
        '''
        return{
            "url": f"{self.base_url}/{self.salt}.{self.extension}",
            "created_at":str(self.created_at)
        }

    def create(self, image_data):
        '''
        Given an image in base64 form, it
        1. Rejects the image is the filetype is not supported
        2. Generates a random string for the image file name
        3. Decodes the image and attempts to upload it to AWS
        '''
        try:
            ext = guess_extension(guess_type(image_data)[0])[1:]

            #only accepts supported file types
            if ext not in EXTENSIONS:
                raise Exception(f"Unsupportted file type: {ext}")


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
            img_data = base64.b63decode(img_str)
            img = Image.open(BytesIO(img_data))

            self.base_url = S3_BASE_URL
            self.salt = salt
            self.extension = ext
            self.width = img.width
            self.height = img.length
            self.created_at = datetime.datetime.now()

            img_filename = f"{self.salt}.{self.extension}"
            self.upload(img, img_filename)

        except Exception as e:
            print(f"Error when creating image: {e}")

    def upload(self, img, img_filename):
        '''
        Attempt to upload the image to the specified S3 bucket
        '''
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


# code to send notifications/reminders
from db import db
from db import Event
from db import User 
from db import Bucket
from db import Asset

from flask import Flask

# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
db_filename = "bukethaca.db"

# setup config 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

# initialize app
db.init_app(app)
with app.app_context():
    events = Event.query.all()

    for event in events:
        event_time = datetime.fromtimestamp(int(event.date))

        # checks if date already passed
        if event_time < datetime.now():
            db.session.delete(event)
            db.session.commit()
        
        # checks if date and time are equal
        tomorrow = datetime.now() + timedelta(1)
        #comment this if statement out when testing
        if event_time - tomorrow < timedelta(seconds=30):
            account_sid = os.environ['TWILIO_ACCOUNT_SID']
            auth_token = os.environ['TWILIO_AUTH_TOKEN']
            client = Client(account_sid, auth_token)
            reminded = event.users_saved #get the users that need to be reminded about that event
            for u in reminded:
                # Find your Account SID and Auth Token at twilio.com/console
                # and set the environment variables. See http://twil.io/secure
                if u.number is not None:
                    message = client.messages.create(
                        body='Hello there! You have an upcoming event! Please visit the Buckethaca app for more info :)',
                        from_='+13254408918',
                        media_url=['https://demo.twilio.com/owl.png'],
                        to= u.number 
                    )
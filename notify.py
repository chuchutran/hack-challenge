# code to send notifications/reminders
from db import db
from db import Event
from db import User 
from db import Category
from db import Bucket
from db import Asset
# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

import time
from datetime import datetime, timedelta

events = Event.query.all()

for event in events:
    event_time = datetime.fromtimestamp(int(event.get("date")))

    # checks if date already passed
    if event_time < datetime.now():
        db.session.delete(event)
        db.session.commit()
    
    # checks if date and time are equal
    user = User.query.filter_by(id=user_id).first()
    user.get("phone_number")
    reminded = event.get("user_reminders") #get the users that need to be reminded about that event

    yesterday = datetime.now() - timedelta(1)
    if event_time == yesterday:
        for u in reminded:
            # Find your Account SID and Auth Token at twilio.com/console
            # and set the environment variables. See http://twil.io/secure
            account_sid = os.environ['TWILIO_ACCOUNT_SID']
            auth_token = os.environ['TWILIO_AUTH_TOKEN']
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body='Hello there!',
                from_='+13254408918',
                media_url=['https://demo.twilio.com/owl.png'],
                to=reminded.get("phone_number")
            )

        print(message.sid)














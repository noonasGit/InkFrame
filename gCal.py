###### Calendar API part #####
from datetime import date, timedelta, datetime
import os.path
from dataclasses import dataclass
from typing import List
from collections import defaultdict, deque



from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



@dataclass
class gCal_events:
    cal_start : int
    cal_stop : int
    cal_time : int
    cal_summary : str


def get_gCal_events():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    return_data = []
    try:
        #Calendar API part
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            print("Checking credentials...")
            print("Token Expires "+creds.expiry.strftime("%H:%M, %A, %b %-d"))
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                            maxResults=10, singleEvents=True,
                            orderBy='startTime').execute()
        events = events_result.get('items', [])

    except IOError as e:
        print("Error:"+str(e))

    if not events:
        print('No upcoming events found.')
        return return_data
    else:
        print(str(len(events))+' UPCOMING EVENTS')

        #Loop trough calendar events and draw them to buffer
        
        return_data : List[gCal_events]

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summ = event['summary'] 

            if len(start) == 10: #events that are 'whole day'-events
                startdate = datetime.strptime(start,"%Y-%m-%d")
                enddate = datetime.strptime(end,"%Y-%m-%d")
                time = ''
            if len(start) == 25: #events that start at specific time
                startdate = datetime.strptime(start,"%Y-%m-%dT%H:%M:%S%z")
                enddate = datetime.strptime(end,"%Y-%m-%dT%H:%M:%S%z")
                time = startdate.strftime(" (%H:%M)")
            startdate_date = startdate.date()  
            if startdate_date < date.today(): #multi day events, set start date at current date
                startdate = date.today()
                startdate_date = date.today()
            day = startdate.strftime("%a %m-%d")
            week = startdate.strftime("%V")






            gCal_events.cal_start = startdate
            gCal_events.cal_summary = summ
            #print(start + ' ' + summary)
            return_data.append(gCal_events(cal_start = startdate,
                                           cal_stop = enddate,
                                           cal_time = time,
                                    cal_summary = summ))


        #Display buffer on screen for 25 seconds
    return return_data
  
    
def gToken():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("Checking credentials...")
        print(creds.valid)
        print(creds.expiry)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Refresh of token...")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

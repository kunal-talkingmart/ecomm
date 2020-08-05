# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# This is a simple example for a custom action which utters "Hello World!"


from __future__ import print_function
import datetime
import pickle
import os.path
import base64
import sys
import dateutil.parser
import json

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from typing import Any, Text, Dict, List

from datetime import datetime
from datetime import timedelta


from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

SCOPES = ['https://www.googleapis.com/auth/calendar']



def calendar_auth():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    global service

    service = build('calendar', 'v3', credentials=creds)


class ActionMaster(Action):

    def name(self) -> Text:
        return "action_master"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        calendar_auth()

        task_type = tracker.get_slot("task_type")

        print(task_type)

        if(task_type=='create'):
            summary = tracker.get_slot("summary")
            startdatetime = tracker.get_slot("time")


#            start = startdatetime.split(',')[0]+"T"+startdatetime.split(',')[1]+":00"
#            if(int(startdatetime.split(',')[1].split(':')[1])>30):
#                end = startdatetime.split(',')[0]+"T"+str(int(startdatetime.split(',')[1].split(':')[0])+1)+":"+str(int(startdatetime.split(',')[1].split(':')[1])-30)+":00"
#            elif(int(startdatetime.split(',')[1].split(':')[1])==30):
#                end = startdatetime.split(',')[0]+"T"+str(int(startdatetime.split(',')[1].split(':')[0])+1)+":"+str(int(startdatetime.split(',')[1].split(':')[1])-30)+":00"
#            else:
#                end = startdatetime.split(',')[0]+"T"+startdatetime.split(',')[1].split(':')[0]+":"+str(int(startdatetime.split(',')[1].split(':')[1])+30)+":00"
            email_attendees = tracker.get_slot("email_attendees")

            start = startdatetime  # leave it as a string 
#            end = json.dumps((dateutil.parser.parse(startdatetime) + timedelta(minutes=30)),indent=4, sort_keys=True, default=str)
#           end = convert startdatetime to datetime object, add 30 min, then convert everything back into serializable JSON
            end = (dateutil.parser.parse(startdatetime) + timedelta(minutes=30)).isoformat()

            print(summary)
            print(start)
            print(end)
            L = list(map(str, email_attendees.split(', ')))
            attendees_list=[]
            for attendee in L:
                attendees_list.append({'email': attendee})
            print(attendees_list)

            if(summary=='null'):
                summary = email_attendees
            

            event = {
            'summary': summary,
            'start': {
                'dateTime': start,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end,
                'timeZone': 'Asia/Kolkata',
            },
            'attendees': attendees_list,
            'reminders': {
                'useDefault': False,
                'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
                ],
            },
            }

            event = service.events().insert(calendarId='primary', sendUpdates='all', body=event).execute()
            print('Event created: %s' % (event.get('htmlLink')))

            # Change the rasa default time settings to 500 instead of 10 as in link https://forum.rasa.com/t/error-asyncio-task-exception-was-never-retrieve/15511/7

            dispatcher.utter_message("Your Event is successfully created of summary {} at time {}".format(summary, startdatetime))

            return []

        if(task_type=='delete'):
            mail = tracker.get_slot("mail")
            print(mail)

            var = 0
            id_list = []
            temp = False
            id = ''
            event_deleted = None
            page_token = None
            while True:
                events = service.events().list(calendarId='primary', pageToken=page_token).execute()
                for event in events['items']:
                    if 'attendees' in event:
                        for attendee in event['attendees']:
                            # print(attendee['email'], mail)
                            if(attendee['email']==mail):
                                temp = True
                    if(temp):
                        temp = False
                        var += 1
                        id_list.append(event['id'])
                        print(var, event['summary'])
                if var > 0:
                    event_del = int(input("Enter the serial number of the Event you wish to delete : "))
                    id = id_list[event_del-1]
                page_token = events.get('nextPageToken')
                if not page_token:
                    break

            if var > 0:
                event_deleted = service.events().get(calendarId='primary', eventId=id).execute()
                service.events().delete(calendarId='primary', eventId=id).execute()
                dispatcher.utter_message("Your Event {} is successfully deleted".format(event_deleted))
            else:
                print("No events to display.")
                dispatcher.utter_message("No events to display")

            return [SlotSet("event_deleted", event_deleted)]

        if(task_type=='list'):
            page_token = None
            while True:
                events = service.events().list(calendarId='primary', pageToken=page_token).execute()
                if not events['items']:
                    print("No events to display")
                    dispatcher.utter_message("No events to display")
                else:
                    for event in events['items']:
                        print(event)
                page_token = events.get('nextPageToken')
                if not page_token:
                    break

            return []

        if(task_type=='free slots'):
            start = tracker.get_slot("start")
            end = tracker.get_slot("end")

            if(start=='none'):
                end_year = int(end.split('-')[0])
                end_month = int(end.split('-')[1])
                end_date = int(end.split('-')[2])
                if(end_date==1):
                    if(end_month==1):
                        start_year = end_year-1
                        start_month = 12
                        start_date = 31
                    elif(end_month==5 or end_month==7 or end_month==8 or end_month==10 or end_month==12):
                        start_year = end_year
                        start_month = end_month-1
                        start_date = 30
                    elif(end_month==2 or end_month==4 or end_month==6 or end_month==9 or end_month==11):
                        start_year = end_year
                        start_month = end_month-1
                        start_date = 31
                    elif(end_month==3):
                        if(end_year%4==0):
                            start_year = end_year
                            start_month = 2
                            start_date = 29
                        else:
                            start_year = end_year
                            start_month = 2
                            start_date = 28
                else:
                    start_year = end_year
                    start_month = end_month
                    start_date = end_date-1
            elif(end=='none'):
                start_year = int(start.split('-')[0])
                start_month = int(start.split('-')[1])
                start_date = int(start.split('-')[2])
                if(start_month==2):
                    if(start_year%4==0 and start_date==29):
                        end_year = start_year
                        end_month = 3
                        end_date = 1
                    elif(start_date==28):
                        end_year = start_year
                        end_month = 3
                        end_date = 1
                    else:
                        end_year = start_year
                        end_month = 2
                        end_date = start_date+1
                elif(start_date==31):
                    if(start_month==12):
                        end_year = start_year+1
                        end_month = 1
                        end_date = 1
                    elif(start_month==1 or start_month==3 or start_month==5 or start_month==7 or start_month==8 or start_month==10):
                        end_year = start_year
                        end_month = start_month+1
                        end_date = 1
                elif(start_date==30):
                    if(start_month==4 or start_month==6 or start_month==9 or start_month==11):
                        end_year = start_year
                        end_month = start_month+1
                        end_date = 1
                else:
                    end_year = start_year
                    end_month = start_month
                    end_date = start_date+1
            else:
                end_year = int(end.split('-')[0])
                end_month = int(end.split('-')[1])
                end_date = int(end.split('-')[2])
                start_year = int(start.split('-')[0])
                start_month = int(start.split('-')[1])
                start_date = int(start.split('-')[2])
            
            startdatetime = str(start_year)+"-"+str(start_month)+"-"+str(start_date)+"T"+"08:00:00+05:30"
            enddatetime = str(end_year)+"-"+str(end_month)+"-"+str(end_date)+"T"+"20:00:00+05:30"

                    
            print(startdatetime)
            print(enddatetime)


            freebusy = service.freebusy().query(body=
                {
                "timeMin": startdatetime,
                "timeMax": enddatetime,
                "timeZone": "+05:30",
                "items": [
                    {
                        "id": 'primary'
                    }
                ]
                }).execute()

            # print(type(freebusy['calendars']['primary']['busy']))

            freeslots = []
            # interval = input("Please give the time of slot in hrs")

            def compareDates_1lt2(date1, date2):
                date1_year = int(date1.split("T")[0].split("-")[0])
                date1_month = int(date1.split("T")[0].split("-")[1])
                date1_date = int(date1.split("T")[0].split("-")[2])
                date2_year = int(date2.split("T")[0].split("-")[0])
                date2_month = int(date2.split("T")[0].split("-")[1])
                date2_date = int(date2.split("T")[0].split("-")[2])

                if(date1_year>date2_year):
                    return False
                elif(date1_year<date2_year):
                    return True
                else:
                    if(date1_month>date2_month):
                        return False
                    elif(date1_month<date2_month):
                        return True
                    else:
                        if(date1_date>date2_date):
                            return False
                        elif(date1_date<=date2_date):
                            return True


            def slotsFromEvents(start, end, busytimes):
                index = 0
                for time in busytimes:
                    if(index==0 and compareDates_1lt2(start, time['start'])):
                        freeslots.append({'start': start, 'end': time['start']})
                    elif(index==0):
                        start = time['end']
                    elif(compareDates_1lt2(busytimes[index-1]['end'], time['start'])):
                        freeslots.append({'start': busytimes[index-1]['end'], 'end': time['start']})
                    if(len(busytimes)==(index+1) and compareDates_1lt2(time['end'], end)):
                        freeslots.append({'start': time['end'], 'end': end})
                    index = index+1
                
                if(len(busytimes)==0):
                    freeslots.append({'start': start, 'end': end})

                # temp = {}
                # hourSlots = []
                # index1 = 0
                # for slot in freeslots:

            slotsFromEvents(startdatetime, enddatetime, freebusy['calendars']['primary']['busy'])

            print(freebusy['calendars']['primary']['busy'])
            print(freeslots)

            dispatcher.utter_message("The free slots are {}".format(freeslots))

            return [SlotSet("freeslots", freeslots)]

        if(task_type=='update'):
            id = tracker.get_slot("id")

            event = service.events().get(calendarId='primary', eventId=id).execute()

            summary = tracker.get_slot("summary")
            startdatetime = tracker.get_slot("startdatetime")
            start = startdatetime.split(',')[0]+"T"+startdatetime.split(',')[1]+":00"
            if(int(startdatetime.split(',')[1].split(':')[1])>30):
                end = startdatetime.split(',')[0]+"T"+str(int(startdatetime.split(',')[1].split(':')[0])+1)+":"+str(int(startdatetime.split(',')[1].split(':')[1])-30)+":00"
            elif(int(startdatetime.split(',')[1].split(':')[1])==30):
                end = startdatetime.split(',')[0]+"T"+str(int(startdatetime.split(',')[1].split(':')[0])+1)+":"+str(int(startdatetime.split(',')[1].split(':')[1])-30)+":00"
            else:
                end = startdatetime.split(',')[0]+"T"+startdatetime.split(',')[1].split(':')[0]+":"+str(int(startdatetime.split(',')[1].split(':')[1])+30)+":00"
            
            
            email_attendees = tracker.get_slot("email_attendees")

            L = list(map(str, email_attendees.split(', ')))
            attendees_list=[]
            for attendee in L:
                attendees_list.append({'email': attendee})
            print(attendees_list)

            if(summary=='null'):
                summary = email_attendees

            event['summary'] = summary
            event['start']['dateTime'] = start
            event['end']['dateTime'] = end
            event['attendees'] = attendees_list


            updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
            
            print('Event updated: %s' % (updated_event.get('htmlLink')))

            dispatcher.utter_message("Your Event is successfully updated of summary {} at time {}".format(summary, startdatetime))

            return []

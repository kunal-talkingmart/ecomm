## create path   <!-- main create event -->
* greet    <!-- initial greeting -->
  - utter_greet  <!-- three choices; translate buttons into intents -->
* request_appointment  <!-- user selects the create option -->
  - slot{"task_type": "create"}
  - utter_ask_startdatetime  <!-- static utterance, asking for a convenient time slot -->
* inform{"time": "2020-06-25,12:00"}  <!-- some words, followed by a time to be interpreted by duckling -->
  - utter_ask_attendees
* inform{"email_attendees": "rishi39@gmail.com"}
  - slot{"summary": "this is a test event"}
  - action_master
  - utter_event_success
* thanks
  - utter_goodbye






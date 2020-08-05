

## create path
* greet
  - utter_greet
  - utter_intro
* event_create
  - utter_ask_summary
* known_summary
  - utter_ask_location
* known_location
  - utter_ask_description
* known_description
  - utter_ask_startdatetime
* known_startdatetime
  <!-- - utter_ask_enddatetime -->
<!-- * known_enddatetime -->
  - utter_ask_attendees
* known_attendees
  - action_create
* thanks
  - utter_goodbye

## delete path
* greet
  - utter_greet
  - utter_intro
* event_delete
  - action_delete
* thanks
  - utter_goodbye

## list path
* greet
  - utter_greet
  - utter_intro
* event_list
  - action_list
* thanks
  - utter_goodbye


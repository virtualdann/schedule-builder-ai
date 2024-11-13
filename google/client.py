import os 
import json
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate_google_calendar():
	creds = None
	# check if token.json exists for saved credentials
	if os.path.exists('token.json'):
		creds = Credentials.from_authorized_user_file('token.json', SCOPES)
	# if not authenticated or expired prompt login
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				'google/credentials.json', SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for future use
		with open('token.json', 'w') as token:
			token.write(creds.to_json())
	return creds


# Google Calendar API Client
def get_calendar_service():
	creds = authenticate_google_calendar()
	service = build('calendar', 'v3', credentials=creds)
	return service


def get_events(maxResult):
	service = get_calendar_service()
	now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
	print(f"Getting the upcoming {maxResult} events")
	events_result = (
		service.events()
		.list(
			calendarId="primary",
			timeMin=now,
			maxResults=maxResult,
			singleEvents=True,
			orderBy="startTime",
		)
		.execute()
	)
	events = events_result.get("items", [])

	if not events:
		print("No upcoming events found.")
		return

	# Prints the start and name of the next 10 events
	result = []
	for event in events:
		start = event["start"].get("dateTime", event["start"].get("date"))
		result.append({
				"start_time": start,
				"event": event["summary"]
			})
	return result


def add_event_to_calendar(summary, description, start_time, end_time):
	service = get_calendar_service()
	event = {
		'summary': summary,
		'description': description,
		'start': {
			'dateTime': start_time,
			'timeZone': 'America/Los_Angeles',  # Use your timezone
		},
		'end': {
			'dateTime': end_time,
			'timeZone': 'America/Los_Angeles',
		},
	}
	event = service.events().insert(calendarId='primary', body=event).execute()
	print(f"Event created: {event.get('htmlLink')}")
	return event


def delete_event(event_id):
	service = get_calendar_service()
	service.events().delete(calendarId='primary', eventId=event_id).execute()
	print(f"Event {event_id} deleted.")


def search_events(query, time_min, time_max):
	service = get_calendar_service()
	events_result = service.events().list(calendarId='primary', q=query, timeMin=time_min,
											timeMax=time_max, singleEvents=True,
											orderBy='startTime').execute()
	events = events_result.get('items', [])
	for event in events:
		print(event['summary'], event['start']['dateTime'], event['end']['dateTime'])
	return events

if __name__ == '__main__':
	try:
	    get_events(10)

	except HttpError as error:
		print(f"An error occurred: {error}")

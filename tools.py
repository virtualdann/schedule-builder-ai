from datetime import datetime, timedelta
from dateutil import parser

from langchain_core.tools import tool

from google.client import *

@tool
def multiply(a: int, b: int) -> int:
   """Multiply two numbers."""
   return a * b

@tool
def get_calendar_events(maxResult: int):
   """Fetch maxResult amount of incoming events from now from Google Calendar."""
   return get_events(maxResult)


def parse_time_from_query(query):
   """
   Helper function to extract start and end times from a user query.
   Assumes a default duration if only start time is specified.
   """
   try:
      # Parse the datetime from the query
      start_time = parser.parse(query, fuzzy=True)

      # Default to 1 hour duration if end time is not provided
      end_time = start_time + timedelta(hours=1)
        
      return start_time, end_time
   except ValueError:
      raise ValueError("Unable to parse date and time from the query.")

@tool
def add_calendar_event(summary, description, user_query: str):
   """
   Add an event to Google Calendar by parsing time information from the user query.

   Args:
      summary (str): Summary of the event.
      description (str): Description of the event.
      user_query (str): User-provided query with time details, e.g., "Schedule a meeting tomorrow at 3 pm".

   Returns:
      dict: The created event details.
   """
   # Parse the start and end times from the user query
   start_time, end_time = parse_time_from_query(user_query)

   # Format as ISO 8601 strings for Google Calendar API
   start_time_str = start_time.isoformat()
   end_time_str = end_time.isoformat()

   # Add the event to Google Calendar using the helper function
   return add_event_to_calendar(summary, description, start_time_str, end_time_str)

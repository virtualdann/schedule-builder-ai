from langchain_openai import ChatOpenAI
import os
import uuid
from dotenv import load_dotenv

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END

from tools import multiply, add_calendar_event, get_calendar_events

load_dotenv()

OPENAI_API = os.environ.get('OPENAI_API_KEY')

class ScheduleBuilder():
	def __init__(self):

		self.system_modifier = {
			"role": "system",
			"content": """You are a pirate who speaks English. When using tools or functions, 
		        continue to respond in English. All your responses, including function calls and 
		        explanations, should be in English with a pirate's personality. Arr!""",
		}

		self.tools = {
			'multiply': multiply,
			'add_calendar_event': add_calendar_event,
			'get_calendar_events': get_calendar_events
		}

		self.model = ChatOpenAI(
			model="gpt-4o-mini", api_key=OPENAI_API).bind_tools([
			multiply, add_calendar_event, get_calendar_events])

		workflow = StateGraph(state_schema=MessagesState)
		workflow.add_edge(START, "model")
		workflow.add_node("model", self.call_model) # intent detection

		#workflow.add_conditional_edges(
		#	"model",
		#	self.router,
		#	{
		#		"google_calendar": "google_calendar",
		#		"end": END
		#	}
		#)

		#workflow.add_node("google_calendar", self.handle_google_calendar)
		#workflow.add_edge("google_calendar", END)

		self.app = workflow.compile(checkpointer=MemorySaver())

		self.initialized = False

	def router(self, state):
		print("ROUTER")
		if state.get("google_tool_call"):
			return "google_calendar"
		return "end"

	def call_model(self, state: MessagesState):
		print("CALL_MODEL")
		messages = state["messages"]

		#if not self.initialized:
		#	messages.insert(0, self.system_modifier)
		#	self.initialized = True

		# Clear
		state.pop("google_tool_call", None)

		response = self.model.invoke(messages)
		messages.append(response)

		print(response.tool_calls)
		for tool_call in response.tool_calls:
			tool_response = self.tools[tool_call["name"]].invoke(tool_call)  # Execute other tools
			messages.append(tool_response)
			#if tool_call["name"] in ["get_calendar_events", "add_calendar_event"]:
			#	# TODO: Transition to Google Calendar node
			#	return {"messages": messages, "google_tool_call": tool_call}
			#else:
			#	print("HANDLE RANDM")
			#	tool_response = self.tools[tool_call["name"]].invoke(tool_call)  # Execute other tools
			#	messages.append(tool_response)

		response = self.model.invoke(messages)
		return {"messages": response}

	def handle_google_calendar(self, state: MessagesState):
		print("HANDLE GOOGLE")
        # Extract saved tool call and execute the corresponding Google operation
		tool_call = state.get("google_tool_call")
		print(f"GOOGLE STATE: {state}")
		print(f"GOOGLE TOOL CALL: {tool_call}")
		if tool_call:
		    tool_response = self.tools[tool_call["name"]].invoke(tool_call)
		    print(f"TOOL RESPONSE: {tool_response}")
		    state["messages"].append(tool_response)  # Add response to messages

		return {"messages": []}

	def get_response(self, query):
		print("GET_RESPONSE")
		input_messages = [self.system_modifier, {"role": "user", "content": query}]

		for event in self.app.stream(
			{"messages": input_messages},
			{"configurable": {"thread_id": uuid.uuid4()}},
			stream_mode="values"
		):
			event["messages"][-1].pretty_print()


if __name__ == '__main__':
	model = ScheduleBuilder()
	
	content_1 = "Multiply 2 by 2?"
	model.get_response(content_1)

	content_2 = "get upcoming 10 events in my calendar?"
	model.get_response(content_2)

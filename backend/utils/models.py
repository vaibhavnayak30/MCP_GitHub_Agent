from typing import Annotated, TypedDict, Literal
from pydantic import BaseModel
from langchain_core.messages import AnyMessage, BaseMessage
from langgraph.graph.message import add_messages

# Define the state of the graph
class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    iteration: int = 0

class InvokeResponse(BaseModel):
    response: Literal[
        "user",
        "assistant",
        "assistant_thinking",
        "assistant_response",
        "tool_output",
        "tool_call_detected",
        "user_input_processed",
        "error",
        "assistant_final_answer",
        "graph_ended",
        "agent_tool_planning",
        "agent_response",
        "user_message_processed",
        "tool_output_received",
        "tool_execution_start",
        "interrupted",
        "stream_error",
        "serialization_error"
    ]
    content : str

class InvokeRequest(BaseModel):
    query: str
    thread_id: str

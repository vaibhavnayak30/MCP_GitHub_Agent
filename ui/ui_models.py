import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# --- API Models ---
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

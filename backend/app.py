# Import standard libraries
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage

# Import custom modules
from utils.logger import AppLogger
from agents.agent import ReactGraphAgent
from utils.models import InvokeRequest, InvokeResponse

# --- Lifespan Management ---
# Define async context manager for lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan management for the app
    """
    # Initialize logger
    logger = AppLogger(__name__).get_logger()

    # Initialize the agent
    app.agent = ReactGraphAgent(logger)
    await app.agent.initiate()

    # Yield the agent to the app
    yield

    # Close the agent
    await app.agent.close()

# --- FastAPI App ---
app = FastAPI(name= "main_agent", lifespan= lifespan)

# --- Routes ---
@app.post("/invoke")
async def invoke_agent(query: InvokeRequest):
    """
    Stream the agent's response
    """
    async def generate_stream():
        # Iterate over raw state changes yielded by agent.stream_invoke
        try:
            async for state_change in app.agent.stream_invoke(query= query.query, thread_id= query.thread_id):
                response_to_send : InvokeResponse | None = None

                if "__end__" in state_change:
                    final_message = state_change["__end__"].get("messages", [])
                    if final_message:
                        last_msg = final_message[-1]
                        if isinstance(last_msg, AIMessage):
                            response_to_send = InvokeResponse(
                                response= "assistant_final_answer",
                                content= last_msg.content
                            )
                        else:
                            response_to_send = InvokeResponse(
                                response= "graph_ended",
                                content= f"Graph finished. Last message type: {type(last_msg).__name__}"
                            )
                    else:
                        response_to_send = InvokeResponse(
                            response= "graph_ended",
                            content= "Graph finished. No messages in the final state."
                        )
                    if response_to_send:
                        yield f"data: {response_to_send.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # Process agent messages (output from the 'agent' node)
                elif "agent" in state_change and "messages" in state_change["agent"]:
                    last_msg = state_change["agent"]["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        if last_msg.tool_calls:
                            # Agent has decided to call tools
                            response_to_send = InvokeResponse(
                                response= "agent_tool_planning",
                                content= f"Agent is calling tools: {', '.join(tool.get('name') for tool in last_msg.tool_calls)} tool(s)."
                            )
                        else:
                            logger.info(f"Assistant message detected: {last_msg.content}")
                            response_to_send = InvokeResponse(
                                response= "assistant_response",
                                content= last_msg.content
                            )
                    elif isinstance(last_msg, HumanMessage):
                        logger.info(f"Human message detected: {last_msg.content}")
                        response_to_send = InvokeResponse(
                            response= "user_input_processed",
                            content= last_msg.content
                        )

                # Process tools messages (output from the 'tools' node)
                elif "tools" in state_change and "messages" in state_change["tools"]:
                    last_msg = state_change["tools"]["messages"][-1]
                    if isinstance(last_msg, ToolMessage):
                        # Tool execution output received
                        response_to_send = InvokeResponse(
                            response= "tool_output_received",
                            content= f"Tool name: {last_msg.name}\nOutput: {last_msg.content}"
                        )
                    elif isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        # This case might indicate the tool node is about to execute tools
                        response_to_send = InvokeResponse(
                            response= "tool_execution_start",
                            content= f"Executing tool(s)."
                        )
                if response_to_send:
                    try:
                        json_response = response_to_send.model_dump_json()
                        yield f"data: {json_response}\n\n"
                    except Exception as e:
                        # Handle serialization errors gracefully
                        error_result = InvokeResponse(
                            response= "serialization_error",
                            content= f"Error serializing response: {str(e)}"
                        )
                        yield f"data: {error_result.model_dump_json()}\n\n"
                else:
                    # If no specific response type is matched, do nothing or log
                    pass
        except Exception as e:
            # Catch any unexpected errors during stream generation
            error_result = InvokeResponse(
                response= "stream_error",
                content= f"Error streaming agent response: {str(e)}"
            )
            yield f"data: {error_result.model_dump_json()}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    return StreamingResponse(generate_stream(), media_type="text/event-stream")

# --- Main ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8003, reload=True)

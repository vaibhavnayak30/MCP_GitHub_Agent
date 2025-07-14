import streamlit as st
import httpx
import asyncio
import uuid
from utils.models import InvokeRequest, InvokeResponse # Corrected import from ui_models to utils.models

# --- Configuration ---
FASTAPI_BACKEND_URL = "http://localhost:8003"

# --- Streamlit App ---
st.set_page_config(page_title="MCP Demo", layout="centered")
st.title("MCP Demo App")

# Initialize chat history (FOR UI DISPLAY ONLY)
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I assist you with repository information or general queries?"})
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.initial_greeting_sent = False

# Display chat messages from history on app rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Check if the message is a structured response (from the assistant with thinking content)
        if msg["role"] == "assistant" and msg.get("type") == "structured_response":
            if msg["thinking_content"]:
                with st.expander("Agent Thinking Process"):
                    st.markdown(msg["thinking_content"])
            st.markdown(msg["main_content"])
        else:
            st.markdown(msg["content"])

# Function to send messages to FastAPI and stream response
async def send_chat_message_and_stream(user_message: str, thread_id: str):
    placeholder = st.empty()
    main_response_content = ""
    thinking_process_content = ""

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream(
                "POST",
                f"{FASTAPI_BACKEND_URL}/invoke",
                json=InvokeRequest(query=user_message, thread_id=thread_id).model_dump(),
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk_bytes in response.aiter_bytes():
                    chunk_text = chunk_bytes.decode('utf-8')
                    buffer += chunk_text

                    parts = buffer.split('\n\n')
                    buffer = parts.pop()

                    for part in parts:
                        if part.startswith('data: '):
                            json_string = part[len('data: '):]
                            if json_string == '[DONE]':
                                print("Stream DONE signal received.")
                                placeholder.empty()
                                return main_response_content, thinking_process_content

                            try:
                                parsed_data = InvokeResponse.model_validate_json(json_string)

                                if parsed_data.response in ["assistant", "assistant_response", "assistant_final_answer"]:
                                    if main_response_content:
                                        main_response_content += "\n\n" + parsed_data.content
                                    else:
                                        main_response_content += parsed_data.content
                                elif parsed_data.response == "agent_tool_planning":
                                    if thinking_process_content and not thinking_process_content.endswith('\n'):
                                        thinking_process_content += "\n"
                                    thinking_process_content += f"\n*Agent is planning: {parsed_data.content}*\n\n"
                                elif parsed_data.response == "tool_output_received":
                                    if thinking_process_content and not thinking_process_content.endswith('\n'):
                                        thinking_process_content += "\n"
                                    thinking_process_content += f"\n*Tool Output: {parsed_data.content}*\n"
                                elif parsed_data.response in ["stream_error", "serialization_error", "error"]:
                                    st.error(f"Agent Error: {parsed_data.content}")
                                    thinking_process_content += f"\n\n[ERROR: {parsed_data.content}]\n"

                                # Update the temporary placeholder
                                combined_streaming_display = ""
                                if thinking_process_content:
                                    combined_streaming_display += thinking_process_content
                                if main_response_content:
                                    if thinking_process_content:
                                        combined_streaming_display += "\n---\n"
                                    combined_streaming_display += main_response_content

                                placeholder.markdown(combined_streaming_display + "▌")

                            except Exception as e:
                                print(f"Error parsing SSE data: {e} | Raw data: {json_string}")
                                st.error(f"Error processing streamed data: {e}. Raw: {json_string[:100]}...")
                                combined_streaming_display = ""
                                if thinking_process_content:
                                    combined_streaming_display += thinking_process_content
                                combined_streaming_display += f"\n\n[STREAM PARSE ERROR]\n"
                                placeholder.markdown(combined_streaming_display + "▌")


        except httpx.RequestError as e:
            st.error(f"Error connecting to backend: {e}. Is the FastAPI server running at {FASTAPI_BACKEND_URL}?")
            print(f"HTTPX Request Error: {e}")
            return f"Error connecting to backend: {e}", ""
        except httpx.HTTPStatusError as e:
            st.error(f"Backend returned an HTTP error: {e.response.status_code} - {e.response.text}")
            print(f"HTTPX Status Error: {e}")
            return f"Backend returned an HTTP error: {e.response.status_code} - {e.response.text}", ""
        except Exception as e:
            st.error(f"An unexpected error occurred during streaming: {e}")
            print(f"Unexpected Streaming Error: {e}")
            return f"An unexpected error occurred during streaming: {e}", ""

    # Fallback
    return main_response_content, thinking_process_content


# --- Main Streamlit Chat Input and Display Logic ---
if prompt := st.chat_input("Ask me about repositories or anything else..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        main_content, thinking_content = asyncio.run(send_chat_message_and_stream(prompt, st.session_state.thread_id))

        # Render the thinking content
        if thinking_content:
            with st.expander("Agent Thinking Process"):
                st.markdown(thinking_content)

        # Render the main assistant
        st.markdown(main_content)

        # Store the structured response
        st.session_state.messages.append({
            "role": "assistant",
            "type": "structured_response",
            "main_content": main_content,
            "thinking_content": thinking_content
        })

    st.rerun()

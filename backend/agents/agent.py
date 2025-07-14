# Import standard libraries
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# Import custom modules
from utils.llm import get_llm
from utils.models import GraphState, InvokeResponse
from utils.prompt import get_agentprompt

class ReactGraphAgent:
    def __init__(self, logger: logging.Logger):
        self.llm = get_llm()
        self.tools = None
        self.logger = logger
        self.agent_graph = None
        self.tool_node_instance = None
        self.agent_prompt = self._get_agent_prompt()

    async def get_tools(self):
        try:
            client = MultiServerMCPClient(
                {
                    "math": {
                        "transport": "streamable_http",
                        "url": "http://127.0.0.1:9002/mcp/",
                    }
                }
            )
            self.tools = await client.get_tools()
            self.logger.info(f"Tools available to the agent: {len(self.tools) if self.tools else 0} tools loaded")
        except Exception as e:
            self.logger.error(f"Error getting tools: {e}", exc_info=True)
            self.tools = []
            raise RuntimeError(f"Tool loading failed: {str(e)}")

    async def _tool_execution_node(self, state: GraphState) -> dict:
        self.logger.info("Entering custom tool execution node...")
        try:
            if not self.tool_node_instance:
                self.tool_node_instance = ToolNode(self.tools)
            messages = state.get("messages", [])
            if not messages:
                self.logger.warning("No messages to process in tool node.")
                return {"messages": [AIMessage(content="No tool calls to process.")]}
            tool_output_dict = await self.tool_node_instance.ainvoke({"messages": messages})
            self.logger.info(f"Tool output dict: {tool_output_dict}")
            return tool_output_dict
        except Exception as e:
            self.logger.error(f"Error in custom tool execution node: {e}", exc_info=True)
            return {"messages": [AIMessage(content=f"An error occurred during tool execution: {str(e)}")]}

    def _should_continue(self, state: GraphState) -> str:
        try:
            messages = state.get("messages", [])
            if not messages:
                self.logger.warning("No messages in state, ending conversation.")
                return END
            last_message = messages[-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                self.logger.info("Tool calls detected, switching to tools node.")
                return "tools"
            self.logger.info("No tool calls detected, ending conversation.")
            return END
        except Exception as e:
            self.logger.error(f"Error checking if agent should continue: {str(e)}", exc_info=True)
            return END

    async def _agent(self, state: GraphState) -> GraphState:
        try:
            messages = state.get("messages", [])
            if not messages:
                self.logger.error("No messages in state for agent to process.")
                return {"messages": [AIMessage(content="I don't see any messages to respond to.")]}
            if not self.tools:
                self.logger.warning("No tools available for the agent to use.")
                llm_with_tools = self.llm
            else:
                llm_with_tools = self.llm.bind_tools(self.tools)
            self.logger.info(f"Processing {len(messages)} messages with the agent.")
            full_message_history = [SystemMessage(content=self.agent_prompt)] + messages
            response = await llm_with_tools.ainvoke(full_message_history)
            self.logger.info("Agent response generated successfully.")
            return {"messages": [response]}
        except Exception as e:
            self.logger.error(f"Error in agent node: {str(e)}", exc_info=True)
            return {"messages": [AIMessage(content="I encountered an error while processing your request. Please try again.")]}

    async def _compile_agent(self):
        try:
            workflow = StateGraph(GraphState)
            workflow.add_node("agent", self._agent)
            workflow.add_node("tools", self._tool_execution_node)
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {"tools": "tools", END: END}
            )
            workflow.add_edge("tools", "agent")
            memory_store = InMemorySaver()
            self.agent_graph = workflow.compile(checkpointer=memory_store)
            self.logger.info("Agent graph compiled successfully.")
        except Exception as e:
            self.logger.error(f"Error compiling agent: {str(e)}", exc_info=True)
            raise RuntimeError(f"Agent compilation failed: {str(e)}")

    async def initiate(self):
        try:
            self.logger.info("Initializing agent...")
            await self.get_tools()
            if not self.tools:
                raise RuntimeError("No tools available for the agent to use after loading.")
            self.tool_node_instance = ToolNode(self.tools)
            self.logger.info("Tool node instantiated successfully.")
            await self._compile_agent()
            self.logger.info("Agent initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
            raise RuntimeError(f"Agent initialization failed: {str(e)}")

    async def stream_invoke(self, query: str, thread_id: str):
        try:
            if not self.agent_graph:
                raise RuntimeError("Agent not compiled. Call initiate() first.")
            initiate_state = GraphState(
                messages=[HumanMessage(content=query)],
                iteration=0
            )
            self.logger.info(f"Streaming agent invocation for thread {thread_id}...")
            async for state_change in self.agent_graph.astream(
                initiate_state,
                config={"configurable": {"thread_id": thread_id}}
            ):
                yield state_change
        except Exception as e:
            self.logger.error(f"Error streaming agent output: {str(e)}", exc_info=True)
            yield {"error": {"messages": str(e)}}

    async def invoke(self, query: str, thread_id: str) -> InvokeResponse:
        try:
            if not self.agent_graph:
                raise RuntimeError("Agent not compiled. Call initiate() first.")
            state = GraphState(
                messages=[HumanMessage(content=query)],
                iteration=0
            )
            self.logger.info(f"Invoking agent for thread {thread_id}...")
            result = await self.agent_graph.ainvoke(
                state,
                config={"configurable": {"thread_id": thread_id}}
            )
            self.logger.info("Agent invocation completed successfully.")
            ai_response_content = "No AI response found."
            if result and "messages" in result and result["messages"]:
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        ai_response_content = msg.content
                        break
            return InvokeResponse(
                response="assistant_final_answer",
                content=ai_response_content
            )
        except Exception as e:
            self.logger.error(f"Error invoking agent: {str(e)}", exc_info=True)
            return InvokeResponse(
                response="error",
                content=f"I encountered an error while processing your request: {str(e)}. Please try again."
                )
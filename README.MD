# AI Agent for querying GITHUB via MCP
GitHub Agent with LangGraph, FastAPI, and Streamlit
This project demonstrates a conversational AI agent designed to interact with the GitHub API via MCP(Model Context Protocol). It leverages LangGraph for orchestrating the agent's logic, FastAPI for exposing the agent's endpoint, and Streamlit for a user-friendly chat interface.

The agent can search repositories, list user repositories, fetch branches, commits, and issues for a given repository, all by intelligently calling the appropriate tools.

✨ **Features:**
- Conversational AI: Interact with the GitHub API using natural language.

- ReAct Style Agent: Agent reasons, plans, acts (tool calls), observes, and renders responses iteratively.

- Tool Use: Integrates with a custom set of GitHub tools exposed via FastMCP.

- Repository Disambiguation: Automatically searches for repositories by keyword and asks for clarification if multiple matches are found.

- Streaming Responses: Provides real-time updates on the agent's thinking process and tool execution via streamable-http protocol.

- Modular Architecture: Separates concerns into distinct services (Tool Server, Agent Backend, Frontend).

## 🚀 Architecture Overview
The application is composed of three main services that communicate with each other:

**GitHub Tools Server (FastMCP Based):**

- A Python server built with fastmcp that exposes a set of GitHub API functionalities (search repositories, get branches, commits, issues, user repos) as callable tools.

- Runs on http://127.0.0.1:9002.

- Authenticates with GitHub using a Personal Access Token.

**Agent Backend (FastAPI):**

- A Python server built with FastAPI that hosts the ReactGraphAgent.

- The ReactGraphAgent uses LangGraph to define the agent's workflow, which includes an LLM (Azure OpenAI) and the GitHub tools from the FastMCP server.

- Provides a streaming /invoke endpoint for real-time interaction.

- Runs on http://127.0.0.1:8003

**Streamlit Frontend:**

- A Python web application built with Streamlit that provides the chat interface.

- Communicates with the FastAPI Agent Backend via HTTPX to send user queries and receive streaming responses.

- Displays the agent's main responses and its internal thinking process (tool calls, observations) in a structured manner.

## 🛠️ Setup and Installation
Follow these steps to get the application up and running on your local machine.

**Prerequisites:**
- Python 3.9+

- Git (for cloning the repository)

- A GitHub Personal Access Token (PAT) with repo scope (for get_all_user_repo, get_all_branches, get_all_commits, get_all_issues).

- Configure Environment Variables
Create a **.env** file in the root directory of your project and populate it with your API keys and endpoints.

## 🛠️GitHub Personal Access Token
GITHUB_TOKEN="your_github_personal_access_token_here"

## 📄 Example Queries:

"Hello!"

"What are all the repositories you have access to?"

"Search for repositories related to 'langchain'."

"Get branches for octocat/Spoon-Knife."

"Show me the commits for octocat/Spoon-Knife."

"List issues for octocat/Spoon-Knife."

"What is the latest commit in octocat/Spoon-Knife?" (Requires the agent to process commit dates)

Observe how the "Agent Thinking Process" expander updates in real-time, showing the agent's internal thoughts, tool calls, and tool outputs.

## 🔮 Future Enhancements
- **More GitHub Tools:** Add tools for creating issues, pulling requests, managing webhooks, etc.

- **Persistent Checkpointing:** Replace InMemorySaver in LangGraph with a persistent store (e.g., SQLite, Redis, Firestore) for long-term conversation history.

- **Authentication for Frontend:** Implement user authentication for the Streamlit app.

- **Error Handling UI:** More sophisticated error display and recovery options in the frontend.

- **Deployment:** Instructions and configurations for deploying the services to cloud platforms (e.g., Azure Container Apps, Kubernetes).

- **Rate Limit Handling:** Implement more robust rate limit handling for GitHub API calls.

## 📄 License
MIT, Apache 2.0
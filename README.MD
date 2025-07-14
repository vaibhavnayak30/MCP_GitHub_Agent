GitHub Agent with LangGraph, FastAPI, and Streamlit
This project demonstrates a conversational AI agent designed to interact with the GitHub API using a ReAct (Reasoning and Acting) pattern. It leverages LangGraph for orchestrating the agent's logic, FastMCP for exposing GitHub tools as microservices, FastAPI for the agent's backend API, and Streamlit for a user-friendly chat interface.

The agent can search repositories, list user repositories, fetch branches, commits, and issues for a given repository, all by intelligently calling the appropriate tools.

✨ Features
Conversational AI: Interact with the GitHub API using natural language.

ReAct Pattern: Agent reasons, plans, acts (tool calls), observes, and renders responses iteratively.

Tool Use: Integrates with a custom set of GitHub tools exposed via FastMCP.

Repository Disambiguation: Automatically searches for repositories by keyword and asks for clarification if multiple matches are found.

Streaming Responses: Provides real-time updates on the agent's thinking process and tool execution via Server-Sent Events (SSE).

Modular Architecture: Separates concerns into distinct services (Tool Server, Agent Backend, Frontend).

Secure Authentication: Uses Azure AD for authenticating with Azure OpenAI and GitHub Personal Access Token for GitHub API access.

🚀 Architecture Overview
The application is composed of three main services that communicate with each other:

GitHub Tools Server (FastMCP):

A Python server built with fastmcp that exposes a set of GitHub API functionalities (search repositories, get branches, commits, issues, user repos) as callable tools.

Runs on http://127.0.0.1:9002.

Authenticates with GitHub using a Personal Access Token.

Agent Backend (FastAPI):

A Python server built with FastAPI that hosts the ReactGraphAgent.

The ReactGraphAgent uses LangGraph to define the agent's workflow, which includes an LLM (Azure OpenAI) and the GitHub tools from the FastMCP server.

Provides a streaming /invoke endpoint for real-time interaction.

Runs on http://127.0.0.1:8003.

Authenticates with Azure OpenAI using Azure AD.

Streamlit Frontend:

A Python web application built with Streamlit that provides the chat interface.

Communicates with the FastAPI Agent Backend via HTTPX to send user queries and receive streaming responses.

Displays the agent's main responses and its internal thinking process (tool calls, observations) in a structured manner.

🛠️ Setup and Installation
Follow these steps to get the application up and running on your local machine.

Prerequisites
Python 3.9+

Git (for cloning the repository)

A GitHub Personal Access Token (PAT) with repo scope (for get_all_user_repo, get_all_branches, get_all_commits, get_all_issues).

Generate a PAT here

An Azure OpenAI Service deployment with a chat model (e.g., gpt-4, gpt-35-turbo).

Azure AD authentication setup for your Azure OpenAI resource. This typically involves granting your user account, service principal, or managed identity the "Cognitive Services OpenAI User" role on the Azure OpenAI resource.

1. Clone the Repository
git clone <repository_url>
cd <repository_name> # Replace with your actual repository name

2. Create a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

3. Install Dependencies
Install all required Python packages for both the backend and frontend.

pip install -r requirements.txt
# If you don't have a requirements.txt, install individually:
# pip install fastmcp PyGithub uvicorn fastapi python-dotenv langchain-openai azure-identity streamlit httpx pydantic

4. Configure Environment Variables
Create a .env file in the root directory of your project and populate it with your API keys and endpoints.

# .env file

# GitHub Personal Access Token
GITHUB_TOKEN="your_github_personal_access_token_here"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://your-aoai-resource-name.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-02-01" # Or your specific API version, e.g., 2023-05-15
AZURE_OPENAI_CHAT_DEPLOYMENT="your-chat-model-deployment-name" # e.g., gpt-4, gpt-35-turbo

# For Azure AD authentication (EnvironmentCredential will pick these up if set)
# AZURE_CLIENT_ID="<your-service-principal-app-id>"
# AZURE_TENANT_ID="<your-tenant-id>"
# AZURE_CLIENT_SECRET="<your-service-principal-secret>"
# Or ensure you are logged in via Azure CLI: `az login`

5. Run the FastMCP GitHub Tools Server
This server must be running first, as the FastAPI agent backend depends on it.

python tools/github_mcp_server.py

You should see output similar to:
INFO:root:Github client initiated
INFO:     Uvicorn running on http://127.0.0.1:9002 (Press CTRL+C to quit)

6. Run the FastAPI Agent Backend
Open a new terminal window (keep the FastMCP server running) and activate your virtual environment.

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

python main_agent.py

You should see output similar to:
INFO:root:Agent initialized successfully.
INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)

7. Run the Streamlit Frontend
Open a third terminal window (keep both servers running) and activate your virtual environment.

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

streamlit run streamlit_app.py

This will open the Streamlit application in your web browser, typically at http://localhost:8501.

💡 Usage
Once the Streamlit app is running, you can interact with the GitHub Agent in the chat interface.

Example Queries:

"Hello!"

"What are all the repositories you have access to?"

"Search for repositories related to 'langchain'."

"Get branches for octocat/Spoon-Knife."

"Show me the commits for octocat/Spoon-Knife."

"List issues for octocat/Spoon-Knife."

"What is the latest commit in octocat/Spoon-Knife?" (Requires the agent to process commit dates)

Observe how the "Agent Thinking Process" expander updates in real-time, showing the agent's internal thoughts, tool calls, and tool outputs.

📁 Project Structure
.
├── agents/
│   ├── __init__.py
│   └── agent.py              # LangGraph ReactGraphAgent implementation
├── tools/
│   ├── __init__.py
│   └── github_mcp_server.py  # FastMCP server exposing GitHub tools
├── utils/
│   ├── __init__.py
│   ├── llm.py                # Azure OpenAI LLM initialization
│   ├── logger.py             # Custom application logger
│   └── models.py             # Pydantic models for GraphState, InvokeRequest, InvokeResponse
├── main_agent.py             # FastAPI backend for the LangGraph agent
├── streamlit_app.py          # Streamlit frontend for the chat interface
├── ui_models.py              # (Optional) Duplicated Pydantic models for frontend (can be removed)
├── .env                      # Environment variables (create this file)
├── requirements.txt          # Project dependencies (create this file)
└── README.md                 # This file

Note on ui_models.py: If streamlit_app.py and the backend code are in the same Python project, ui_models.py is a duplicate of utils/models.py. It's recommended to remove ui_models.py and import InvokeRequest and InvokeResponse directly from utils.models in streamlit_app.py for a single source of truth.

🔮 Future Enhancements
More GitHub Tools: Add tools for creating issues, pulling requests, managing webhooks, etc.

Persistent Checkpointing: Replace InMemorySaver in LangGraph with a persistent store (e.g., SQLite, Redis, Firestore) for long-term conversation history.

Authentication for Frontend: Implement user authentication for the Streamlit app.

Error Handling UI: More sophisticated error display and recovery options in the frontend.

Deployment: Instructions and configurations for deploying the services to cloud platforms (e.g., Azure Container Apps, Kubernetes).

Rate Limit Handling: Implement more robust rate limit handling for GitHub API calls.

📄 License
MIT, Apache 2.0
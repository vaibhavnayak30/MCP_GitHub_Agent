import asyncio
import logging
from fastmcp import FastMCP
from contextlib import asynccontextmanager
from github import Github, Auth
from typing import Union, Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Lifespan Management ---
# Define async context manager for lifespan management
@asynccontextmanager
async def lifespan(app: FastMCP):
    """
    Lifespan management for the FastMCP server
    """
    # Initiate github client
    auth = Auth.Token("<YOUR_GITHUB_PAT_TOKEN>")
    app.github_client = Github(auth=auth)
    logger.info("Github client initiated")
    # Release the client
    yield
    # Close the client
    logger.info("Closing github client")
    app.github_client.close()

# --- MCP Server ---
# Set the instance of mcp server
mcp = FastMCP(name="github_mcp_server", lifespan= lifespan)

# --- MCP Tools ---
# Define the tools
@mcp.tool()
async def search_repositories_by_keyword(keyword: str) -> Union[List[Dict[str, str]], str]:
    """
    Searches for GitHub repositories that match a given keyword in their name or description.
    This tool is useful when the full repository name (owner/repo_name) is unknown.

    Args:
    - keyword (str): A keyword or partial name to search for in repository names and descriptions.

    Output format:
    A list of dictionaries, where each dictionary represents a matching repository
    and contains its 'full_name' (e.g., "owner/repo_name") and 'description'.
    Example: [{"full_name": "octocat/Spoon-Knife", "description": "This is a test repo."},
              {"full_name": "another-user/knife-utils", "description": "Utilities for knife-related operations."}]
    Returns an empty list if no repositories are found.
    Returns a string error message if an exception occurs.
    """
    try:
        results = mcp.github_client.search_repositories(query=keyword)
        found_repos = []
        for repo in results:
            found_repos.append({"full_name": repo.full_name, "description": repo.description or "No description provided."})

            # Limit results
            if len(found_repos) >= 2:
                break

        if not found_repos:
            return f"No repositories found matching '{keyword}'."
        return found_repos

    except Exception as e:
        logger.error(f"Error searching repositories for keyword '{keyword}': {e}")
        return f"Error searching repositories: {e}"


@mcp.tool()
async def get_all_user_repo() -> Union[list[str], str]:
    """
    Get all repository names associated with the authenticated GitHub user.

    Output format:
    A list of strings, where each string is the full name of a repository (e.g., "owner/repo_name").
    Example: ["vaibhavnayak30/API_Security", "octocat/hello-world"]
    Returns a string error message if an exception occurs.
    """
    try:
        # Initialize the list of repositories
        repo_list = []

        # Get all repositories of a user
        for repo in mcp.github_client.get_user().get_repos():
            repo_list.append(repo.full_name)

        # Return the list of repositories
        return repo_list

    except Exception as e:
        logger.error(f"Error getting all repositories: {e}")
        return f"Error getting all repositories: {str(e)}"

@mcp.tool()
async def get_all_branches(repo_name: str) -> Union[list[str], str]:
    """
    Get all branch names for a specified GitHub repository.

    Args:
    - repo_name (str): The full name of the repository (e.g., "octocat/Spoon-Knife").

    Output format:
    A list of strings, where each string is the name of a branch.
    Example: ["main", "dev", "feature/new-design"]
    Returns a string error message if an exception occurs (e.g., repository not found).
    """
    try:
        branches = []
        # Select the repo
        repo = mcp.github_client.get_repo(repo_name)

        # Get all branches of the repo
        for branch in repo.get_branches():
            branches.append(branch.name)

        return branches

    except Exception as e:
        logger.error(f"Error getting all repositories: {e}")
        return f"Error fething branches: {str(e)}"


@mcp.tool()
async def get_all_commits(repo_name: str) -> Union[Dict[str, str], str]:
    """
    Get all commits of a specified GitHub repository, along with their author names and commit dates.

    Args:
    - repo_name (str): The full name of the repository (e.g., "octocat/Spoon-Knife").

    Output format:
    A dictionary where keys are commit dates (in string format) and values are the names of the commit authors.
    Example: {"2024-06-18 10:30:00+00:00": "John Doe", "2024-06-17 15:00:00+00:00": "Jane Smith"}
    Returns a string error message if an exception occurs (e.g., repository not found).
    """
    try:
        # Select the repo
        repo = mcp.github_client.get_repo(repo_name)

        # Initialize the dictionary
        commit_author_date: dict = {}

        # Get all branches of the repo
        for commit in repo.get_commits():
            # Append to commits_date dict
            commit_author_date[str(commit.commit.author.date)] = str(commit.commit.author.name)

        return commit_author_date

    except Exception as e:
        logger.error(f"Error getting all commits: {e}")
        return f"Error getting all commits: {e}"


@mcp.tool()
async def get_all_issues(repo_name: str) -> str:
    """
    Get all issues of a specified GitHub repository, including their title, number, and body.

    Args:
    - repo_name (str): The full name of the repository (e.g., "octocat/Spoon-Knife").

    Output format:
    A list of strings, where each string provides details for one issue in the format:
    "Issue Title : [title], Issue Number : [number], Issue Body : [body]".
    Example: ["Issue Title : Bug in login, Issue Number : 1, Issue Body : Users cannot log in", "Issue Title : Feature request, Issue Number : 2, Issue Body : Add dark mode"]
    Returns a string error message if an exception occurs (e.g., repository not found).
    """
    try:
        # Select the repo
        repo = mcp.github_client.get_repo(repo_name)

        # Initialize the list of issues
        issue_list = []

        # Get all issues of the repo
        for issue in repo.get_issues():
            issue_list.append(f"Issue Title : {issue.title}, Issue Number : {issue.number}, Issue Body : {issue.body}")

        return issue_list

    except Exception as e:
        logger.error(f"Error getting all commits: {e}")
        return f"Error getting all commits: {e}"


async def main():
    await mcp.run_async(transport="streamable-http", host="127.0.0.1", port=9002)

if __name__ == "__main__":
    asyncio.run(main())

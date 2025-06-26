import os
import json
import importlib
from datetime import datetime
import requests
from logger import get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# logger
logger = get_logger(__name__)

def load_plugins():
    """Load all plugins from the plugins directory"""
    plugins = []
    plugins_dir = "plugins"
    
    # Ensure plugins directory exists
    if not os.path.exists(plugins_dir):
        return plugins
    
    # Find all Python files in plugins directory
    for file in os.listdir(plugins_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = file[:-3]  # Remove .py extension
            try:
                # Import the plugin module
                plugin = importlib.import_module(f"plugins.{module_name}")
                plugins.append(plugin)
                logger.debug(f"Loaded plugin: {module_name}")
            except Exception as e:
                logger.error(f"Error loading plugin {module_name}: {e}")
    
    return plugins

def collect_plugin_data(plugins):
    """Collect data from all plugins"""
    collected_data = {}
    
    for plugin in plugins:
        try:
            # Assume each plugin has a get_data or similar function
            if hasattr(plugin, 'run'):
                plugin_name = plugin.__name__.split('.')[-1]
                data = plugin.run()
                collected_data[plugin_name] = data
        except Exception as e:
            logger.error(f"Error collecting data from plugin {plugin.__name__}: {e}")
    
    return collected_data

def upload_to_knowledge_base(data):
    """Upload collected data to ElevenLabs knowledge base"""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    # Convert data to formatted text
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"plugin_data_{timestamp}.txt"
    path = os.path.join("output",filename)
    # Create a formatted text representation of the data
    formatted_data = f"Plugin Data Collection - {timestamp}\n\n"
    for plugin_name, plugin_data in data.items():
        formatted_data += f"=== {plugin_name} ===\n"
        formatted_data += json.dumps(plugin_data, indent=2)
        formatted_data += "\n\n"
    
    # Save to temporary file
    try:
        with open(path, 'w') as f:
            f.write(formatted_data)
    except Exception as e:
        logger.erro("Error writing to file: " + e)
    
    # Upload to ElevenLabs
    headers = {
        "Xi-api-key": ELEVENLABS_API_KEY,
        "Api-Key": "xi-api-key"
    }
    
    args = {
        'name': "plugin_data_",  # Use the actual filename
    }

    try:
        with open(path, 'rb') as f:
            files = {
                'file': (filename, f, 'text/plain'),
            }
            response = requests.post(
                f"{ELEVENLABS_API_URL}/convai/knowledge-base/file",
                headers=headers,
                data=args,
                files=files,
            )
            print(response.json())
    except Exception as e:
        logger.error("error saving file: " + str(e))

    if response.status_code != 200:
        raise Exception(f"Failed to upload to knowledge base: {response.text}")
    return response.json()

def update_agent_knowledge(knowledge_base_id):
    """Update the agent to use the new plugin data knowledge base, replacing the old plugin data file but preserving others."""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    agent_id = os.getenv('ELEVENLABS_AGENT_ID')
    if not agent_id:
        raise ValueError("ELEVENLABS_AGENT_ID not found in environment variables")
    
    # Fetch current agent config to preserve existing knowledge bases
    current_agent = get_agent()
    existing_kbs = []
    try:
        existing_kbs = current_agent["conversation_config"]["agent"]["prompt"].get("knowledge_base", [])
    except Exception as e:
        logger.warning(f"Could not find knowledge_base in agent config: {e}")
    
    # Remove any previous plugin data file (by name or id pattern)
    filtered_kbs = [
        kb for kb in existing_kbs
        if not (kb.get("name", "").startswith("plugin_data_") or kb.get("id", "").startswith("plugin_data_"))
    ]
    
    # Add the new plugin data file
    filtered_kbs.append({
        "type": "file",
        "name": "plugin_data_",
        "id": knowledge_base_id,
        "usage_mode": "auto"
    })
    
    data = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "knowledge_base": filtered_kbs
                }
            }
        }
    }
    
    response = requests.patch(
        f"{ELEVENLABS_API_URL}/convai/agents/{agent_id}",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to update agent: {response.text}")
    
    return response.json()

def get_agent():
    """Get the current agent configuration"""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    agent_id = os.getenv('ELEVENLABS_AGENT_ID')
    if not agent_id:
        raise ValueError("ELEVENLABS_AGENT_ID not found in environment variables")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    response = requests.get(
        f"{ELEVENLABS_API_URL}/convai/agents/{agent_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get agent: {response.text}")
    
    return response.json()

def delete_documents_by_name(name):
    """
    Search all knowledge base documents with the given name and delete them.
    Args:
        name (str): The name of the document(s) to delete.
    Returns:
        list: List of deleted document IDs.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    deleted_ids = []
    # Paginate through all documents
    next_cursor = None
    while True:
        params = {"page_size": 100}
        if next_cursor:
            params["cursor"] = next_cursor
        response = requests.get(
            f"{ELEVENLABS_API_URL}/convai/knowledge-base",
            headers=headers,
            params=params
        )
        if response.status_code != 200:
            raise Exception(f"Failed to list knowledge base documents: {response.text}")
        data = response.json()
        documents = data.get("documents", [])
        for doc in documents:
            if name == doc.get("name"):
                doc_id = doc.get("id")
                del_resp = requests.delete(
                    f"{ELEVENLABS_API_URL}/convai/knowledge-base/{doc_id}?force=true",
                    headers=headers
                )
                if del_resp.status_code == 204:
                    logger.info(f"Successfully deleted document f{doc_id}")
                    deleted_ids.append(doc_id)
                else:
                    logger.warning(f"Failed to delete document {doc_id}: {del_resp.text}")
        if not data.get("has_more"):
            break
        next_cursor = data.get("next_cursor")

def delete_files_by_prefix(directory, prefix):
    """
    Delete all files in the specified directory that start with the given prefix.
    Args:
        directory (str): Path to the directory.
        prefix (str): Filename prefix to match.
    Returns:
        list: List of deleted file paths.
    """
    deleted_files = []
    if not os.path.isdir(directory):
        raise ValueError(f"{directory} is not a valid directory")
    for filename in os.listdir(directory):
        if filename.startswith(prefix):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
    return deleted_files

def main():
    try:
        # Delete all "plugin_data_" documents from KB.
        logger.info("Deleting 'plugin_data_' documents from knowledge base...")
        delete_documents_by_name("plugin_data_")
        logger.info("Deleting 'plugin_data_' documents from local...")
        print(delete_files_by_prefix("output","plugin_data_"))
        # Load all plugins
        plugins = load_plugins()
        if not plugins:
            logger.warning("No plugins found!")
            return
        
        # Collect data from plugins
        logger.info("Collecting data from plugins...")
        data = collect_plugin_data(plugins)
        
        # Upload to knowledge base
        logger.info("Uploading data to knowledge base...")
        kb_response = upload_to_knowledge_base(data)
        knowledge_base_id = kb_response['id']
        logger.info(f"Successfully uploaded to knowledge base with ID: {knowledge_base_id}")
        # Update agent
        logger.info("Updating agent with new knowledge base...")
        agent_response = update_agent_knowledge(knowledge_base_id)
        logger.info("Successfully updated agent configuration")
        
        # Verify agent configuration
        logger.info("Verifying agent configuration...")
        agent = get_agent()
        logger.info("Current agent configuration:")
        try:
            kbs = agent["conversation_config"]["agent"]["prompt"].get("knowledge_base", [])
            if kbs:
                logger.info("Knowledge bases:")
                for kb in kbs:
                    logger.info(f"- ID: {kb.get('id')}")
                    logger.info(f"- Name: {kb.get('name')}")
                    logger.info(f"  Type: {kb.get('type')}")
                    logger.info(f"  Usage mode: {kb.get('usage_mode')}")
            else:
                logger.warning("No knowledge bases configured")
        except Exception as e:
            logger.warning(f"Could not find knowledge_base in agent config: {e}")
        # TODO: Clean up files locally AND in elevenlabs knowledge base.
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main() 
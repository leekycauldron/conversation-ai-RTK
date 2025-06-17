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
    filename = os.path.join("output",f"plugin_data_{timestamp}.txt")
    
    # Create a formatted text representation of the data
    formatted_data = f"Plugin Data Collection - {timestamp}\n\n"
    for plugin_name, plugin_data in data.items():
        formatted_data += f"=== {plugin_name} ===\n"
        formatted_data += json.dumps(plugin_data, indent=2)
        formatted_data += "\n\n"
    
    # Save to temporary file
    try:
        with open(filename, 'w') as f:
            f.write(formatted_data)
    except Exception as e:
        logger.erro("Error writing to file: " + e)
    
    # Upload to ElevenLabs
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        files = {
            'file': (filename, open(filename, 'rb'), 'text/plain')
        }
    except Exception as e:
        logger.error("error saving file: " + e)

    
    with open(filename, 'rb') as f:
            files = {
                'file': (filename, f, 'text/plain')
            }
            
            response = requests.post(
                f"{ELEVENLABS_API_URL}/convai/knowledge-base/file",
                headers=headers,
                files=files
            )
        
    if response.status_code != 200:
        raise Exception(f"Failed to upload to knowledge base: {response.text}")
    return response.json()

def update_agent_knowledge(knowledge_base_id):
    """Update the agent to use the new knowledge base"""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Note: You would need to replace AGENT_ID with your actual agent ID
    agent_id = os.getenv('ELEVENLABS_AGENT_ID')
    if not agent_id:
        raise ValueError("ELEVENLABS_AGENT_ID not found in environment variables")
    
    # Update agent configuration to use the new knowledge base
    data = {
        "conversation_config": {
            "agent" :{
                "prompt":{
                    "knowledge_base": [{
                        "type": "file",
                        "name": knowledge_base_id,
                        "id": knowledge_base_id,
                        "usage_mode": "auto"
                    }]
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

def main():
    try:
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
        logger.info("\nVerifying agent configuration...")
        agent = get_agent()
        logger.info("\nCurrent agent configuration:")
        if "knowledge_base" in agent.get("agent", {}):
            logger.info("Knowledge bases:")
            for kb in agent["agent"]["knowledge_base"]:
                logger.info(f"- ID: {kb.get('id')}")
                logger.info(f"  Type: {kb.get('type')}")
                logger.info(f"  Usage mode: {kb.get('usage_mode')}")
        else:
            logger.warning("No knowledge bases configured")
        # TODO: Agent Knowledge RAG.
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main() 
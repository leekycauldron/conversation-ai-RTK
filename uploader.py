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

def upload_to_knowledge_base():
    """Upload collected data to ElevenLabs knowledge base"""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    filename = f"facts.txt"
    
    # Upload to ElevenLabs
    headers = {
        "Xi-api-key": ELEVENLABS_API_KEY,
        "Api-Key": "xi-api-key"
    }
    
    args = {
        'name': "facts",  # Use the actual filename
    }

    try:
        with open(filename, 'rb') as f:
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
        if not (kb.get("name", "").startswith("facts") or kb.get("id", "").startswith("facts"))
    ]
    
    # Add the new plugin data file
    filtered_kbs.append({
        "type": "file",
        "name": "facts",
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

def main():
    try:
        # Upload to knowledge base
        logger.info("Uploading data to knowledge base...")
        kb_response = upload_to_knowledge_base()
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

    except Exception as e:
        logger.error(f"Error: {e}")

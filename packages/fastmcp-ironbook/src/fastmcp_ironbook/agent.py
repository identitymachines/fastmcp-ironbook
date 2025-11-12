"""Agent identification and registration with Iron Book."""

import logging
from typing import Optional, Tuple
from ironbook_sdk import IronBookClient, RegisterAgentOptions

logger = logging.getLogger(__name__)


def identify_agent(client_info_cache: dict) -> Tuple[str, str, Optional[str], str]:
    """
    Identify agent from MCP clientInfo (captured during initialize).
    
    Per MCP specification, clientInfo is provided during the initialize phase.
    
    Args:
        client_info_cache: Cache containing MCP client info
    
    Returns:
        Tuple of (agent_name, agent_key, client_version, identification_method)
    """
    mcp_client = client_info_cache.get("default")
    if mcp_client:
        client_name = mcp_client["name"].lower().replace(" ", "-")
        client_version = mcp_client.get("version")
        
        if client_version:
            agent_name = f"{client_name}-agent-v{client_version}"
        else:
            agent_name = f"{client_name}-agent"
            
        logger.info(f"Agent identified via MCP clientInfo: {agent_name}")
        return (agent_name, agent_name, client_version, "mcp-clientinfo")
    
    logger.warning("No MCP clientInfo available, using unknown agent")
    return ("unknown-agent", "unknown-agent", None, "default")


def extract_agent_capabilities(client_info_cache: dict, agent_name: str) -> list:
    """
    Extract capabilities from MCP client capabilities captured during initialize.
    
    Returns MCP capability names directly (e.g., "roots", "sampling").
    Returns empty list if no MCP capabilities available.
    
    Args:
        client_info_cache: Cache containing MCP client info
        agent_name: Name of the agent
    
    Returns:
        List of MCP capability names
    """
    mcp_client = client_info_cache.get("default")
    if mcp_client and "capabilities" in mcp_client:
        mcp_capabilities = mcp_client["capabilities"]
        if mcp_capabilities:
            # Ensure capabilities is a dict
            if isinstance(mcp_capabilities, dict):
                capability_list = list(mcp_capabilities.keys())
                logger.info(f"Using MCP capabilities: {capability_list}")
                return capability_list
            else:
                logger.warning(f"Capabilities is not a dict type: {type(mcp_capabilities)}")
    
    logger.warning(f"No MCP capabilities found for agent {agent_name}")
    return []


async def get_or_register_agent(
    ironbook_client: IronBookClient,
    client_info_cache: dict,
    agent_registry: dict,
    developer_did: str = "did:web:identitymachines.com"
) -> dict:
    """
    Get or register an agent based on the client type.
    
    Agent identity is determined from MCP clientInfo.name captured during
    the initialize hook per MCP specification.
    
    Args:
        ironbook_client: Iron Book SDK client instance
        client_info_cache: Cache containing MCP client info
        agent_registry: Registry to cache agent registrations
        developer_did: Developer DID for agent registration
    
    Returns:
        Agent info dict for policy decisions
    """
    agent_name, agent_key, client_version, identification_method = identify_agent(client_info_cache)
    
    # Fetch organization settings to get org ID
    try:
        org_settings = await ironbook_client.get_org_settings()
        org_id = org_settings.org_id
        # Append org ID to agent name for better identification
        agent_name_with_org = f"{agent_name}-{org_id}"
        logger.info(f"Organization ID retrieved: {org_id}, agent name updated to: {agent_name_with_org}")
    except Exception as e:
        logger.warning(f"Failed to fetch org settings: {e}. Using agent name without org ID.")
        agent_name_with_org = agent_name
        org_id = None
    
    if agent_key in agent_registry:
        logger.info(f"Using cached agent registration for {agent_name_with_org}")
        return agent_registry[agent_key].copy()
    
    logger.info(f"Registering new agent: {agent_name_with_org}")
    
    capabilities = extract_agent_capabilities(client_info_cache, agent_name_with_org)
    
    register_options = RegisterAgentOptions(
        agent_name=agent_name_with_org,
        capabilities=capabilities,
        developer_did=developer_did
    )
    
    try:
        registered = await ironbook_client.register_agent(register_options)
        
        agent_info = {
            "agent_did": registered["agentDid"],
            "developer_did": registered["developerDid"],
            "vc": registered["vc"],
            "agent_name": agent_name_with_org,
            "agent_version": client_version,
            "capabilities": capabilities,
            "identification_method": identification_method,
            "org_id": org_id,
        }
        agent_registry[agent_key] = agent_info
        
        logger.info(
            f"Successfully registered agent: {agent_info['agent_did']} "
            f"(identified via: {identification_method})"
        )
        return agent_info
        
    except Exception as e:
        error_msg = str(e)
        
        if "already exists" in error_msg.lower() or "409" in error_msg:
            logger.warning(f"Agent {agent_name_with_org} already registered with Iron Book")
            logger.info(f"Fetching existing agent details from Iron Book for {agent_name_with_org}")
            
            filtered_agent_name = ''.join(c for c in agent_name_with_org if c.isalnum())
            agent_did = f"did:web:agents.identitymachines.com:{filtered_agent_name}"
            
            logger.info(f"Attempting to fetch agent with DID: {agent_did}")
            
            try:
                existing_agent = await ironbook_client.get_agent(agent_did)
                
                logger.info(f"Successfully fetched existing agent: {existing_agent.did}")
                
                agent_info = {
                    "agent_did": existing_agent.did,
                    "developer_did": existing_agent.developer_did or developer_did,
                    "vc": existing_agent.vc,
                    "agent_name": agent_name_with_org,
                    "agent_version": client_version,
                    "capabilities": capabilities,
                    "identification_method": identification_method,
                    "trust_score": existing_agent.trust_score,
                    "status": existing_agent.status,
                    "org_id": org_id,
                    "note": "Fetched existing agent from Iron Book with valid VC"
                }
                agent_registry[agent_key] = agent_info
                
                logger.info(f"Policy enforcement available for {agent_name_with_org} with fetched VC")
                return agent_info
                
            except Exception as fetch_error:
                logger.error(f"Failed to fetch existing agent from Iron Book: {fetch_error}")
                logger.warning(f"Creating agent info without VC - policy enforcement will be unavailable")
                
                agent_info = {
                    "agent_did": agent_did,
                    "developer_did": developer_did,
                    "vc": None,
                    "agent_name": agent_name_with_org,
                    "agent_version": client_version,
                    "capabilities": capabilities,
                    "identification_method": identification_method,
                    "org_id": org_id,
                    "note": f"Agent exists in Iron Book but fetch failed: {str(fetch_error)}. Policy enforcement disabled.",
                    "policy_enforcement_available": False
                }
                agent_registry[agent_key] = agent_info
                
                return agent_info
        
        logger.error(f"Failed to register agent: {e}")
        raise


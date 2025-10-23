"""Iron Book policy enforcement."""

import os
import logging
from typing import Optional
from ironbook_sdk import IronBookClient, GetAuthTokenOptions, PolicyInput

logger = logging.getLogger(__name__)


async def enforce_policy(
    ironbook_client: IronBookClient,
    agent_info: dict,
    action: str,
    resource: str,
    context: Optional[dict] = None,
    policy_id: str = "policy_a4e4d26bdbfa4c57bc52a67952500cc7"
) -> bool:
    """
    Enforce Iron Book policy before executing a tool.
    
    Gets a fresh auth token for each policy check (tokens are single-use).
    
    Args:
        ironbook_client: Iron Book SDK client instance
        agent_info: Agent information dict
        action: The action being performed
        resource: The resource being accessed
        context: Optional context for policy evaluation
        policy_id: Iron Book policy ID to evaluate
    
    Returns:
        True if allowed
        
    Raises:
        PermissionError: If policy denies access
    """
    if not agent_info.get("vc"):
        logger.error(
            f"Cannot enforce policy: Agent {agent_info.get('agent_name')} has no valid VC. "
            f"Reason: {agent_info.get('note', 'Unknown')}"
        )
        raise PermissionError(
            f"Policy enforcement unavailable: Agent has no valid Verifiable Credential. "
            f"Restart the MCP server to re-register the agent with Iron Book."
        )
    
    base_url = os.getenv("IRONBOOK_BASE_URL", "https://api.ironbook.identitymachines.com")
    
    auth_options = GetAuthTokenOptions(
        agent_did=agent_info["agent_did"],
        vc=agent_info["vc"],
        action=action,
        resource=resource,
        audience=base_url,
        developer_did=agent_info.get("developer_did")
    )
    
    try:
        token_data = await ironbook_client.get_auth_token(auth_options)
        fresh_token = token_data["access_token"]
    except Exception as e:
        logger.error(f"Failed to get Iron Book auth token: {e}")
        raise
    
    full_context = context or {}
    full_context["agent_name"] = agent_info.get("agent_name")
    full_context["capabilities"] = agent_info.get("capabilities", [])
    
    policy_input = PolicyInput(
        agent_did=agent_info["agent_did"],
        policy_id=policy_id,
        token=fresh_token,
        context=full_context
    )
    
    try:
        decision = await ironbook_client.policy_decision(policy_input)
        
        if decision.allow:
            logger.info(
                f"Policy ALLOW: agent={agent_info['agent_did']}, "
                f"action={action}, resource={resource}"
            )
            return True
        else:
            reason = decision.reason or "Policy denied access"
            logger.warning(
                f"Policy DENY: agent={agent_info['agent_did']}, "
                f"action={action}, resource={resource}, reason={reason}"
            )
            raise PermissionError(f"Access denied: {reason}")
            
    except PermissionError:
        raise
    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        raise


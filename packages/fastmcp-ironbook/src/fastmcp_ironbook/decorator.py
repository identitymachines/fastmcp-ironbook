"""Policy enforcement decorator for FastMCP tools."""

import logging
import inspect
from functools import wraps
from typing import Optional, Callable
from fastmcp import FastMCP
from ironbook_sdk import IronBookClient
from .agent import get_or_register_agent
from .policy import enforce_policy

logger = logging.getLogger(__name__)

# Module-level state (initialized via setup)
_mcp_server: Optional[FastMCP] = None
_ironbook_client: Optional[IronBookClient] = None
_client_info_cache: Optional[dict] = None
_agent_registry: Optional[dict] = None
_developer_did: str = "did:web:identitymachines.com"
_default_policy_id: Optional[str] = None


def setup(
    mcp_server: FastMCP,
    ironbook_client: IronBookClient,
    client_info_cache: dict,
    agent_registry: dict,
    developer_did: str = "did:web:identitymachines.com",
    default_policy_id: Optional[str] = None
):
    """
    Initialize the fastmcp-ironbook package with required dependencies.
    
    This must be called once before using the @require_policy decorator.
    
    Args:
        mcp_server: FastMCP server instance
        ironbook_client: Iron Book SDK client instance
        client_info_cache: Dictionary for caching MCP client info
        agent_registry: Dictionary for caching agent registrations
        developer_did: Developer DID for agent registration
        default_policy_id: Default Iron Book policy ID for all tools
    
    Example:
        from fastmcp import FastMCP
        from ironbook_sdk import IronBookClient
        import fastmcp_ironbook
        
        mcp = FastMCP("my-server")
        ironbook = IronBookClient(api_key="...")
        
        fastmcp_ironbook.setup(
            mcp_server=mcp,
            ironbook_client=ironbook,
            client_info_cache={},
            agent_registry={},
            default_policy_id="policy_abc123"
        )
    """
    global _mcp_server, _ironbook_client, _client_info_cache, _agent_registry, _developer_did, _default_policy_id
    
    _mcp_server = mcp_server
    _ironbook_client = ironbook_client
    _client_info_cache = client_info_cache
    _agent_registry = agent_registry
    _developer_did = developer_did
    _default_policy_id = default_policy_id
    
    logger.info("fastmcp-ironbook initialized")


def require_policy(context_fn: Optional[Callable] = None, policy_id: Optional[str] = None):
    """
    Decorator to automatically enforce Iron Book policy on MCP tools.
    
    Automatically sets:
    - action: The name of the decorated function
    - resource: mcp://{server_name}
    
    Note: You must call setup() before using this decorator.
    
    Args:
        context_fn: Optional callable that takes the function's arguments and 
                   returns a context dict for policy evaluation
        policy_id: Optional policy ID to override the default from setup()
    
    Example:
        # Use default policy ID from setup
        @mcp.tool()
        @require_policy()
        async def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        # Override with specific policy ID
        @mcp.tool()
        @require_policy(policy_id="policy_xyz789")
        async def admin_tool() -> str:
            return "Admin operation"
        
        # With context and custom policy
        @mcp.tool()
        @require_policy(
            lambda a, b: {"operation": "addition"},
            policy_id="policy_math123"
        )
        async def add_numbers(a: float, b: float) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check initialization
            if _mcp_server is None:
                raise RuntimeError(
                    "fastmcp-ironbook not initialized. Call fastmcp_ironbook.setup() first."
                )
            
            action = func.__name__
            resource = f"mcp://{_mcp_server.name}"
            
            # Get or register agent
            agent_info = await get_or_register_agent(
                ironbook_client=_ironbook_client,
                client_info_cache=_client_info_cache,
                agent_registry=_agent_registry,
                developer_did=_developer_did
            )
            
            # Build context
            context = {}
            if context_fn:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                context = context_fn(**bound_args.arguments)
            
            # Determine policy ID: decorator override → default → error
            effective_policy_id = policy_id or _default_policy_id
            if not effective_policy_id:
                raise ValueError(
                    f"No policy ID configured for tool '{func.__name__}'. "
                    f"Either provide policy_id to @require_policy() or set default_policy_id in setup()."
                )
            
            # Enforce policy
            await enforce_policy(
                ironbook_client=_ironbook_client,
                agent_info=agent_info,
                action=action,
                resource=resource,
                context=context,
                policy_id=effective_policy_id
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


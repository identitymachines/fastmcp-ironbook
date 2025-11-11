"""MCP client information capture middleware."""

import logging
from fastmcp.server.middleware.middleware import Middleware, MiddlewareContext, CallNext
import mcp.types as mt

logger = logging.getLogger(__name__)


class ClientInfoMiddleware(Middleware):
    """
    Custom middleware to capture MCP client information during initialization.
    
    Implements on_initialize hook per MCP specification:
    https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle#initialization
    
    This provides standardized client identification with name, version, and capabilities.
    """
    
    def __init__(self, cache_dict: dict):
        """
        Initialize middleware with a cache dictionary.
        
        Args:
            cache_dict: Dictionary to store captured client info
        """
        super().__init__()
        self.cache = cache_dict
    
    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequestParams],
        call_next: CallNext[mt.InitializeRequestParams, None],
    ) -> None:
        """Capture clientInfo and capabilities from MCP initialization"""
        try:
            params = context.message.params
            client_info = params.clientInfo if params.clientInfo else None
            capabilities = params.capabilities if params.capabilities else None
            
            # Convert capabilities object to dict for easier handling
            capabilities_dict = {}
            if capabilities:
                try:
                    # Try to convert to dict using vars() or model_dump()
                    if hasattr(capabilities, 'model_dump'):
                        capabilities_dict = capabilities.model_dump()
                    elif hasattr(capabilities, 'dict'):
                        capabilities_dict = capabilities.dict()
                    else:
                        # Fallback: extract attributes
                        capabilities_dict = {k: v for k, v in vars(capabilities).items() if not k.startswith('_')}
                except Exception as e:
                    logger.warning(f"Could not convert capabilities to dict: {e}")
            
            if client_info:
                client_name = client_info.name if hasattr(client_info, 'name') else ""
                client_version = client_info.version if hasattr(client_info, 'version') else ""
                
                capability_names = list(capabilities_dict.keys()) if capabilities_dict else []
                logger.info(
                    f"MCP Initialize: Client connected - {client_name or 'unnamed'} "
                    f"v{client_version or 'unknown'} with capabilities: {capability_names or 'none'}"
                )
                
                if client_name:
                    self.cache["default"] = {
                        "name": client_name,
                        "version": client_version or None,
                        "capabilities": capabilities_dict
                    }
                    logger.info(f"Cached MCP client info: {client_name} v{client_version}")
        except Exception as e:
            logger.warning(f"Failed to validate request: {e}")
        
        return await call_next(context)


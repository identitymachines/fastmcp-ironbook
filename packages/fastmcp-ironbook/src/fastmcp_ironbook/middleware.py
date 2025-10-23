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
        params = context.message.params
        client_info = params.clientInfo if params.clientInfo else {}
        capabilities = params.capabilities if params.capabilities else {}
        
        if client_info:
            client_name = client_info.name if hasattr(client_info, 'name') else ""
            client_version = client_info.version if hasattr(client_info, 'version') else ""
            
            logger.info(
                f"MCP Initialize: Client connected - {client_name or 'unnamed'} "
                f"v{client_version or 'unknown'} with capabilities: {list(capabilities.keys()) if capabilities else 'none'}"
            )
            
            if client_name:
                self.cache["default"] = {
                    "name": client_name,
                    "version": client_version or None,
                    "capabilities": capabilities
                }
                logger.info(f"Cached MCP client info: {client_name} v{client_version}")
        
        return await call_next(context)


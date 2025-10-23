# fastmcp-ironbook

Iron Book agent-based security integration for FastMCP servers.

## Overview

`fastmcp-ironbook` provides a simple way to add Iron Book's agent-based security and policy enforcement to your FastMCP servers. It automatically identifies MCP clients, registers them as agents with Iron Book, and enforces policies on tool calls.

## Features

- **Automatic Agent Registration**: Agents are automatically registered with Iron Book based on MCP client info
- **MCP Specification Compliant**: Uses standard MCP `clientInfo` and `capabilities` from initialization
- **Policy Enforcement**: Integrate Iron Book's policy engine with a simple decorator
- **Version Tracking**: Tracks client versions in agent names (e.g., `cursor-agent-v1.0.0`)
- **Capability-Based Access**: Uses MCP capabilities directly for policy decisions

## Installation

```bash
pip install fastmcp-ironbook
```

## Quick Start

```python
import os
from fastmcp import FastMCP
from ironbook_sdk import IronBookClient
import fastmcp_ironbook
from fastmcp_ironbook import ClientInfoMiddleware, require_policy

# Initialize caches
mcp_client_info_cache = {}
agent_registry = {}

# Initialize Iron Book client
ironbook = IronBookClient(
    api_key=os.getenv("IRONBOOK_API_KEY"),
    base_url=os.getenv("IRONBOOK_BASE_URL", "https://api.ironbook.identitymachines.com")
)

# Create MCP server
mcp = FastMCP("my-server")

# Add middleware to capture client info
mcp.add_middleware(ClientInfoMiddleware(mcp_client_info_cache))

# Initialize fastmcp-ironbook
fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache=mcp_client_info_cache,
    agent_registry=agent_registry,
    default_policy_id="policy_abc123"  # Your Iron Book policy ID
)

# Now you can use the @require_policy decorator on your tools!
@mcp.tool()
@require_policy(lambda name: {"name": name})
async def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

@mcp.tool()
@require_policy(lambda a, b: {"operation": "addition", "a": a, "b": b})
async def add_numbers(a: float, b: float) -> dict:
    """Add two numbers together."""
    result = a + b
    return {
        "result": result,
        "operation": f"{a} + {b} = {result}"
    }

# Run the server
if __name__ == "__main__":
    mcp.run()
```

## How It Works

### 1. Client Identification

The `ClientInfoMiddleware` captures MCP client information during the initialization phase per the [MCP specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle#initialization):

```python
{
  "clientInfo": {
    "name": "Cursor",
    "version": "1.0.0"
  },
  "capabilities": {
    "roots": {"listChanged": true},
    "sampling": {}
  }
}
```

This creates an agent named `cursor-agent-v1.0.0` with capabilities `["roots", "sampling"]`.

### 2. Agent Registration

On the first tool call, the agent is automatically registered with Iron Book:
- Agent name: Based on client name and version
- Capabilities: MCP capabilities from the initialize message
- Developer DID: Configurable (default: `did:web:identitymachines.com`)

### 3. Policy Enforcement

The `@require_policy` decorator automatically:
- Sets `action` to the function name
- Sets `resource` to `mcp://{server_name}`
- Gets/registers the agent
- Enforces the Iron Book policy
- Passes optional context for policy decisions

## API Reference

### setup()

Initialize the package before using the decorator.

```python
fastmcp_ironbook.setup(
    mcp_server: FastMCP,
    ironbook_client: IronBookClient,
    client_info_cache: dict,
    agent_registry: dict,
    developer_did: str = "did:web:identitymachines.com"
)
```

**Parameters:**
- `mcp_server`: Your FastMCP server instance
- `ironbook_client`: Iron Book SDK client instance
- `client_info_cache`: Dictionary for caching MCP client info
- `agent_registry`: Dictionary for caching agent registrations
- `developer_did`: Optional developer DID for agent registration

### @require_policy()

Decorator to enforce Iron Book policy on MCP tools.

```python
@require_policy(context_fn: Optional[Callable] = None)
```

**Parameters:**
- `context_fn`: Optional callable that takes function arguments and returns a context dict

**Examples:**

```python
# No context
@mcp.tool()
@require_policy()
async def simple_tool() -> str:
    return "Hello!"

# With context
@mcp.tool()
@require_policy(lambda data: {"data_length": len(data)})
async def process_data(data: str) -> dict:
    return {"processed": len(data)}
```

### ClientInfoMiddleware

Middleware to capture MCP client information during initialization.

```python
middleware = ClientInfoMiddleware(cache_dict: dict)
mcp.add_middleware(middleware)
```

## Advanced Usage

### Manual Policy Enforcement

If you need more control, you can use the underlying functions directly:

```python
from fastmcp_ironbook import get_or_register_agent, enforce_policy

@mcp.tool()
async def my_tool(param: str) -> dict:
    # Get agent info
    agent_info = await get_or_register_agent(
        ironbook_client=ironbook,
        client_info_cache=mcp_client_info_cache,
        agent_registry=agent_registry
    )
    
    # Enforce policy with custom action/resource
    await enforce_policy(
        ironbook_client=ironbook,
        agent_info=agent_info,
        action="custom_action",
        resource="custom://resource",
        context={"key": "value"}
    )
    
    # Execute tool logic
    return {"result": "success"}
```

### Custom Developer DID

```python
fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache=mcp_client_info_cache,
    agent_registry=agent_registry,
    developer_did="did:web:mycompany.com"
)
```

## Policy Configuration

### Default Policy ID

Set a default policy ID in setup that applies to all tools:

```python
fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache={},
    agent_registry={},
    default_policy_id="policy_abc123"  # Default for all tools
)
```

### Per-Tool Policy Override

Override the default policy for specific tools:

```python
@mcp.tool()
@require_policy(policy_id="policy_admin_xyz")
async def admin_operation() -> dict:
    """Uses policy_admin_xyz instead of default"""
    return {"status": "admin"}

# Or with context and custom policy
@mcp.tool()
@require_policy(
    lambda data: {"data_length": len(data)},
    policy_id="policy_sensitive"
)
async def sensitive_tool(data: str) -> dict:
    return {"processed": len(data)}
```

### Policy ID Priority

1. **Decorator policy_id** (highest priority)
2. **Default policy_id from setup()**
3. **Error if neither provided**

This ensures you never forget to configure a policy.

**Example use cases:**

```python
# Case 1: Single policy for everything
fastmcp_ironbook.setup(..., default_policy_id="policy_main")

@require_policy()
async def tool1(): ...

@require_policy()
async def tool2(): ...
# Both use policy_main

# Case 2: Default + admin override
fastmcp_ironbook.setup(..., default_policy_id="policy_standard")

@require_policy()
async def regular_tool(): ...  # Uses policy_standard

@require_policy(policy_id="policy_admin")
async def admin_tool(): ...  # Uses policy_admin

# Case 3: No default (per-tool required)
fastmcp_ironbook.setup(...)  # No default_policy_id

@require_policy(policy_id="policy_read")
async def read_tool(): ...  # OK

@require_policy()
async def forgot_policy(): ...  # ERROR: No policy ID configured!
```

### Policy Rules

Create policies in Iron Book that check MCP capabilities:

```rego
# Example policy checking for MCP "roots" capability
allow if {
    input.resource == "mcp://my-server"
    input.action == "sensitive_operation"
    "roots" in input.context.capabilities
}
```

## Environment Variables

Required for Iron Book integration:

```bash
IRONBOOK_API_KEY=your_api_key_here
IRONBOOK_BASE_URL=https://api.ironbook.identitymachines.com  # Optional
```

## Requirements

- Python >= 3.10
- fastmcp >= 0.2.0
- ironbook-sdk >= 0.3.0

## License

MIT

## Resources

- [Iron Book Documentation](https://docs.ironbook.identitymachines.com)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)

## Support

For issues and questions:
- GitHub Issues: https://github.com/identitymachines/fastmcp-ironbook/issues
- Email: support@identitymachines.com


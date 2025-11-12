# fastmcp-ironbook

> Add Iron Book's agent-based security to your FastMCP servers with a single decorator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

`fastmcp-ironbook` provides enterprise-grade security for FastMCP servers through automatic agent registration and policy-based authorization powered by Iron Book.

### Key Features

- **Automatic Agent Registration** - MCP clients are automatically registered as agents with Iron Book
- **Policy-Based Authorization** - Fine-grained access control using Open Policy Agent (OPA)
- **MCP Specification Compliant** - Uses standard MCP `clientInfo` and `capabilities`
- **Complete Audit Trail** - All actions logged for compliance (HIPAA, SOC2)
- **Simple Integration** - Add security with a single decorator

## Quick Example

```python
import os
from fastmcp import FastMCP
from ironbook_sdk import IronBookClient
import fastmcp_ironbook
from fastmcp_ironbook import ClientInfoMiddleware, require_policy

# Setup
mcp = FastMCP("my-server")
ironbook = IronBookClient(api_key=os.getenv("IRONBOOK_API_KEY"))

mcp_client_info_cache = {}
agent_registry = {}

mcp.add_middleware(ClientInfoMiddleware(mcp_client_info_cache))

fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache=mcp_client_info_cache,
    agent_registry=agent_registry,
    default_policy_id="policy_abc123"
)

# Secure your tools with one decorator
@mcp.tool()
@require_policy(lambda name: {"name": name})
async def greet(name: str) -> str:
    """Greet a user by name - secured by policy."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

That's it! Your tool is now protected by Iron Book policies.

## Installation

```bash
pip install fastmcp-ironbook
```

## Documentation

### Getting Started

- **[Package Documentation](packages/fastmcp-ironbook/README.md)** - Complete API reference
- **[Healthcare Example](examples/healthcare/README.md)** - Full HIPAA-compliant demo

## Repository Structure

This is a monorepo containing:

```
fastmcp-ironbook/
├── packages/
│   └── fastmcp-ironbook/    # The package (pip install fastmcp-ironbook)
├── examples/
│   └── healthcare/          # HIPAA-compliant medical records demo
└── README.md               # You are here
```

## Real-World Examples

### Healthcare - HIPAA Compliance

Secure medical record access with role-based permissions:

```python
@mcp.tool()
@require_policy(lambda patient_id: {"patient_id": patient_id})
async def get_patient_record(patient_id: str) -> dict:
    """Access patient records with full audit trail."""
    return fetch_patient_data(patient_id)

@mcp.tool()
@require_policy(
    lambda patient_id, rx: {"risk_level": "high" if rx.get("controlled") else "standard"},
    policy_id="policy_prescriptions_xyz"  # Stricter policy
)
async def write_prescription(patient_id: str, prescription: dict) -> dict:
    """Write prescriptions with elevated privileges."""
    return create_prescription(patient_id, prescription)
```

**[View complete example →](examples/healthcare/README.md)**

## How It Works

### 1. Automatic Agent Registration

When an MCP client connects, `fastmcp-ironbook` automatically:
- Identifies the client type from MCP `clientInfo` (Cursor, Claude Desktop, etc.)
- Extracts MCP capabilities (roots, sampling, etc.)
- Registers the agent with Iron Book
- Caches registration for future requests

### 2. Policy Enforcement

The `@require_policy` decorator:
- Gets or registers the agent
- Retrieves a fresh auth token (Iron Book tokens are single-use)
- Sends policy check to Iron Book
- Evaluates using Open Policy Agent (OPA)
- Allows or denies based on policy rules
- Creates audit log entry

### 3. Policy Example

Control access based on MCP capabilities:

```rego
package ironbook.policy

import future.keywords.if
import future.keywords.in

default allow = false

# Allow if agent has 'roots' capability (filesystem access)
allow if {
    input.resource == "mcp://my-server"
    input.action == "get_patient_record"
    "roots" in input.context.capabilities
}
```

## Use Cases

### Multi-Tenant Access Control
Different clients (Cursor, Claude, custom agents) with different permission levels

### HIPAA/SOC2 Compliance
Complete audit trails of who accessed what data and when

### Financial Services
Transaction approval workflows with fraud detection

### Development vs Production
Same tools, different policies based on environment

**[See more examples →](examples/README.md)**

## Benefits

### For Developers
- **Simple Integration**: One decorator to secure tools
- **Type Safe**: Full TypeScript/Python type support
- **Flexible**: Override policies per-tool or use defaults

### For Security Teams
- **Complete Audit Trail**: Every action logged with context
- **Policy-Based**: Centralized access control with OPA
- **Dynamic**: Update policies without code changes

### For Compliance
- **HIPAA Ready**: Full audit logging and access controls
- **SOC2 Compatible**: Policy-based authorization with trails
- **Version Tracking**: Agent versions logged in all actions

## Requirements

- Python >= 3.10
- fastmcp >= 0.2.0
- ironbook-sdk >= 0.3.3

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas we'd love help with:
- Additional examples (financial, admin tools, multi-tenant)
- Documentation improvements
- Bug reports and fixes
- Feature requests

## Resources

### This Project
- [Package Documentation](packages/fastmcp-ironbook/README.md)
- [Examples](examples/)
- [GitHub Issues](https://github.com/identitymachines/fastmcp-ironbook/issues)

### External
- [Iron Book Console](https://ironbook.identitymachines.com)
- [Iron Book Documentation](https://docs.identitymachines.com)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [Open Policy Agent](https://www.openpolicyagent.org)

## Support

- **Package Issues**: [GitHub Issues](https://github.com/identitymachines/fastmcp-ironbook/issues)

## License

MIT - See [LICENSE](LICENSE) for details

---

**Built by [Identity Machines](https://identitymachines.com)** | Powering secure AI agent systems

# Healthcare MCP Server Example

A complete example demonstrating HIPAA-compliant medical record access with Iron Book policy-based authorization.

## Overview

This example shows how to build a secure healthcare data server using FastMCP and Iron Book. It demonstrates:

- **Patient record access** with audit logging
- **Prescription writing** with elevated privileges
- **Lab result uploads** with urgency handling
- **Multi-tier policy enforcement** (default + custom policies)
- **HIPAA compliance** through complete audit trails

## Prerequisites

1. **Python 3.10+**
2. **Iron Book Account**
   - Sign up at [https://ironbook.identitymachines.com](https://ironbook.identitymachines.com)
   - Create an API key
3. **MCP Client** (Cursor, Claude Desktop, or compatible)

## Installation

### 1. Install the Package

If you haven't already installed `fastmcp-ironbook`:

```bash
pip install fastmcp-ironbook
```

Or for local development:

```bash
cd ../../packages/fastmcp-ironbook
pip install -e .
```

### 2. Install Example Dependencies

```bash
cd examples/healthcare
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your Iron Book credentials:

```bash
IRONBOOK_API_KEY=your_ironbook_api_key_here
IRONBOOK_BASE_URL=https://api.ironbook.identitymachines.com
```

## Running the Server

### Testing Locally

```bash
python server.py
```

The server will start in STDIO mode, ready for MCP client connections.

### Integration with Cursor

Add this configuration to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "healthcare-server": {
      "command": "python",
      "args": ["/absolute/path/to/fastmcp-ironbook/examples/healthcare/server.py"],
      "env": {
        "IRONBOOK_API_KEY": "your_ironbook_api_key_here",
        "IRONBOOK_BASE_URL": "https://api.ironbook.identitymachines.com"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/` with the actual path on your system.

### Integration with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "healthcare-server": {
      "command": "python",
      "args": ["/absolute/path/to/fastmcp-ironbook/examples/healthcare/server.py"],
      "env": {
        "IRONBOOK_API_KEY": "your_ironbook_api_key_here",
        "IRONBOOK_BASE_URL": "https://api.ironbook.identitymachines.com"
      }
    }
  }
}
```

## Available Tools

### get_patient_record

Retrieve patient medical records.

**Usage**:
```python
get_patient_record(patient_id="PT-12345")
```

**Returns**:
- Patient demographics
- Current diagnosis
- Active medications
- Allergies
- Visit history

**Policy**: Requires `roots` capability (filesystem access)

### write_prescription

Write prescriptions for patients (elevated privileges).

**Usage**:
```python
write_prescription(
    patient_id="PT-12345",
    prescription={
        "medication": "Amoxicillin",
        "dosage": "500mg",
        "frequency": "Three times daily",
        "controlled": False
    }
)
```

**Policy**: Uses stricter `prescriptions-policy.rego`
- Requires `roots` capability
- Requires approved agent (e.g., Cursor)
- Controlled substances are denied

### upload_lab_results

Upload laboratory test results.

**Usage**:
```python
upload_lab_results(
    patient_id="PT-12345",
    data={
        "test_name": "Complete Blood Count",
        "values": {"wbc": 7500, "rbc": 4.8},
        "abnormal": False
    }
)
```

**Policy**: Requires `roots` capability

### get_agent_status

View current agent's capabilities and access level.

**Usage**:
```python
get_agent_status()
```

**Returns**: Agent identity, capabilities, and healthcare-specific access levels

### get_server_info

Get server metadata and compliance information.

**Usage**:
```python
get_server_info()
```

## Policy Configuration

This example uses two Iron Book policies:

### 1. Default Healthcare Policy (`healthcare-policy.rego`)

Controls standard access to patient records and lab results.

**Rules**:
- Allow record access with `roots` capability
- Allow lab uploads with `roots` capability
- All access logged for HIPAA compliance

### 2. Prescriptions Policy (`prescriptions-policy.rego`)

Stricter policy for prescription writing.

**Rules**:
- Requires `roots` capability
- Only approved agents (e.g., Cursor)
- Standard prescriptions only
- Controlled substances denied

### Uploading Policies to Iron Book

1. Log in to [Iron Book Portal](https://ironbook.identitymachines.com)
2. Navigate to Policies section
3. Create a new policy:
   - **Name**: `healthcare-policy`
   - **Content**: Copy from `policies/healthcare-policy.rego`
   - **Note the Policy ID** (e.g., `policy_abc123`)
4. Create another policy:
   - **Name**: `prescriptions-policy`
   - **Content**: Copy from `policies/prescriptions-policy.rego`
   - **Note the Policy ID**

5. Update `server.py` with your policy IDs:
```python
# Default policy ID (line 51)
default_policy_id="policy_abc123"  # Your healthcare policy ID

# Prescription policy override (line 95)
policy_id="policy_xyz789"  # Your prescriptions policy ID
```

## Testing the Example

### 1. Check Server Status

```python
get_server_info()
```

Expected response includes compliance information and available tools.

### 2. Check Agent Registration

```python
get_agent_status()
```

Verify your agent is registered and has appropriate capabilities.

### 3. Access Patient Record

```python
get_patient_record(patient_id="PT-12345")
```

Should return mock patient data if policy allows.

### 4. Try Writing a Prescription

```python
write_prescription(
    patient_id="PT-12345",
    prescription={
        "medication": "Lisinopril",
        "dosage": "10mg",
        "frequency": "Once daily",
        "controlled": False
    }
)
```

Should succeed if using Cursor with `roots` capability.

### 5. Test Policy Enforcement

Try with a controlled substance:

```python
write_prescription(
    patient_id="PT-12345",
    prescription={
        "medication": "Oxycodone",
        "dosage": "5mg",
        "frequency": "As needed",
        "controlled": True  # This should be denied
    }
)
```

Expected: `PermissionError` due to policy restriction on controlled substances.

## Understanding the Security Model

### Agent-Based Authentication

- **Agent = Client Type** (e.g., `cursor-agent-v1.0.0`)
- Agents are automatically registered with Iron Book
- MCP capabilities determine permissions

### Multi-Tier Policy System

1. **Default Policy** (`healthcare-policy.rego`)
   - Applied to most tools
   - Set in `fastmcp_ironbook.setup(default_policy_id="...")`

2. **Custom Policy** (`prescriptions-policy.rego`)
   - Applied to specific tools via decorator
   - Overrides default policy
   - Example: `@require_policy(..., policy_id="policy_xyz789")`

3. **No Policy** = Error
   - System requires explicit policy configuration
   - Prevents accidental exposure

### Audit Trail

Every action is logged by Iron Book:
- Agent identity
- Action performed
- Resource accessed
- Policy decision
- Timestamp
- Context data

View logs in the [Iron Book Portal](https://ironbook.identitymachines.com) under Audit Logs.

## Customization

### Adding New Tools

```python
@mcp.tool()
@require_policy(lambda arg: {"context_key": arg})
async def my_healthcare_tool(arg: str) -> dict:
    """Tool description."""
    return {"result": "data"}
```

### Modifying Policies

Edit `.rego` files in `policies/` directory and re-upload to Iron Book Console.

### Changing Policy IDs

Update policy IDs in `server.py`:
- Line 51: `default_policy_id`
- Line 95: Tool-specific `policy_id` in decorator

## Troubleshooting

### "No policy ID configured" Error

**Cause**: Policy ID not set in `setup()` or decorator.

**Fix**: Add policy IDs to `server.py` (see "Uploading Policies" section).

### "Access denied" Error

**Cause**: Policy rejected the request.

**Fix**: 
1. Check agent capabilities with `get_agent_status()`
2. Verify policy rules in Iron Book Console
3. Check audit logs for denial reason

### Agent Registration Failed

**Cause**: Iron Book API key invalid or network issue.

**Fix**:
1. Verify `IRONBOOK_API_KEY` in `.env`
2. Check network connectivity
3. View server logs for detailed errors

## Resources

- [fastmcp-ironbook Package Documentation](../../packages/fastmcp-ironbook/README.md)
- [Iron Book Portal](https://ironbook.identitymachines.com)
- [Iron Book Documentation](https://docs.identitymachines.com)
- [MCP Specification](https://modelcontextprotocol.io)

## License

MIT


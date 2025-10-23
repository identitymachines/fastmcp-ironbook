# Healthcare Policy - Standard Access
# This policy controls access to patient medical records
#
# Key Concepts:
# - Agent identity = CLIENT TYPE (cursor-agent-v1.0.0, claude-desktop-agent-v2.1.0, etc.)
# - Policies check MCP capabilities directly (e.g., "roots", "sampling")
# - All access is logged for HIPAA compliance

package ironbook.policy

import future.keywords.if
import future.keywords.in

# Default deny all access
default allow = false

# Allow reading patient records for agents with 'roots' capability
# This represents authenticated healthcare providers with filesystem access
allow if {
    input.resource == "mcp://healthcare-server"
    input.action == "get_patient_record"
    "roots" in input.context.capabilities
}

# Allow uploading lab results for agents with 'roots' capability
allow if {
    input.resource == "mcp://healthcare-server"
    input.action == "upload_lab_results"
    "roots" in input.context.capabilities
}

# Allow agent status checks for all authenticated agents
# This is a read-only operation that doesn't expose sensitive data
allow if {
    input.resource == "mcp://healthcare-server"
    input.action == "get_agent_status"
}

# Allow server info for all authenticated agents
allow if {
    input.resource == "mcp://healthcare-server"
    input.action == "get_server_info"
}

# Time-based restrictions (optional)
# Uncomment to restrict access to business hours
# deny if {
#     # Deny operations outside business hours (9 AM - 5 PM UTC)
#     hour := time.clock([time.now_ns()])[0]
#     hour < 9
# }
# deny if {
#     hour := time.clock([time.now_ns()])[0]
#     hour >= 17
# }

# Example: Restrict specific agents
# Only allow specific agent versions
# deny if {
#     input.action == "get_patient_record"
#     not startswith(input.context.agent_name, "cursor-agent")
# }


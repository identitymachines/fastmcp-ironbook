# Prescriptions Policy - Elevated Access
# This policy enforces stricter rules for prescription writing
#
# Requirements:
# - Agent must have 'roots' capability
# - Agent must be from approved list (e.g., Cursor)
# - High-risk controlled substances are heavily restricted

package ironbook.policy

import future.keywords.if
import future.keywords.in

# Default deny all access
default allow = false

# Allow standard prescriptions for approved agents with 'roots' capability
allow if {
    input.resource == "mcp://healthcare-server"
    input.action == "write_prescription"
    "roots" in input.context.capabilities
    startswith(input.context.agent_name, "cursor-agent")  # Only Cursor agents allowed
    input.context.risk_level == "standard"  # Non-controlled substances only
}

# Deny high-risk prescriptions entirely
# Controlled substances require additional out-of-band verification
deny if {
    input.action == "write_prescription"
    input.context.risk_level == "high"
}

# Additional safety checks
# Deny if patient_id is missing or invalid
deny if {
    input.action == "write_prescription"
    not input.context.patient_id
}

# Example: Require specific agent version for prescriptions
# Uncomment to enforce minimum version requirements
# deny if {
#     input.action == "write_prescription"
#     # Example: Require cursor-agent v2.0.0 or higher
#     version := substring(input.context.agent_name, 13, -1)  # Extract version
#     semver.compare(version, "2.0.0") < 0
# }

# Example: Rate limiting for prescriptions
# Uncomment to limit prescriptions per time window
# deny if {
#     input.action == "write_prescription"
#     # Check if agent has exceeded prescription rate limit
#     # This would require maintaining state in Iron Book
#     count(input.context.recent_prescriptions) > 10
# }


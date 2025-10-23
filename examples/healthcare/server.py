"""
Healthcare MCP Server with Iron Book Integration

HIPAA-compliant medical record access with policy-based authorization.
Demonstrates real-world security scenarios for healthcare data.
"""

import os
import sys
from dotenv import load_dotenv
from fastmcp import FastMCP
from ironbook_sdk import IronBookClient
import logging

# Add packages directory to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages', 'fastmcp-ironbook', 'src'))

# Import from fastmcp-ironbook package
import fastmcp_ironbook
from fastmcp_ironbook import ClientInfoMiddleware, require_policy

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize caches
mcp_client_info_cache = {}
agent_registry = {}

# Initialize Iron Book client
ironbook = IronBookClient(
    api_key=os.getenv("IRONBOOK_API_KEY"),
    base_url=os.getenv("IRONBOOK_BASE_URL", "https://api.ironbook.identitymachines.com")
)

# Create the FastMCP server instance
mcp = FastMCP("healthcare-server")

# Add middleware to capture client info
mcp.add_middleware(ClientInfoMiddleware(mcp_client_info_cache))

# Initialize fastmcp-ironbook package with default healthcare policy
fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache=mcp_client_info_cache,
    agent_registry=agent_registry,
    default_policy_id="policy_a4e4d26bdbfa4c57bc52a67952500cc7"  # Default healthcare policy
)


# === Helper function for getting agent info in tool responses ===

async def get_agent_info() -> dict:
    """
    Helper to get agent info for use in tool responses.
    Uses the package's get_or_register_agent function.
    """
    return await fastmcp_ironbook.get_or_register_agent(
        ironbook_client=ironbook,
        client_info_cache=mcp_client_info_cache,
        agent_registry=agent_registry
    )


# === Healthcare Tools with Policy Enforcement ===

@mcp.tool()
@require_policy(lambda patient_id: {"patient_id": patient_id, "data_type": "medical_record"})
async def get_patient_record(patient_id: str) -> dict:
    """
    Get patient medical record (HIPAA protected).
    
    Requires 'roots' capability for filesystem access.
    All access is logged for audit trail.
    
    Args:
        patient_id: Unique patient identifier
        
    Returns:
        Patient medical record with diagnosis, medications, and history
    """
    # In a real system, this would fetch from a secure database
    # For demo purposes, we return mock data
    
    logger.info(f"Accessing medical record for patient: {patient_id}")
    
    return {
        "patient_id": patient_id,
        "name": "John Doe",
        "dob": "1980-05-15",
        "diagnosis": "Hypertension (Primary)",
        "medications": [
            {"name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"},
            {"name": "Aspirin", "dosage": "81mg", "frequency": "Once daily"}
        ],
        "allergies": ["Penicillin"],
        "last_visit": "2024-10-15",
        "next_appointment": "2025-01-15",
        "notes": "Patient responding well to current treatment plan"
    }


@mcp.tool()
@require_policy(
    lambda patient_id, prescription: {
        "patient_id": patient_id,
        "medication": prescription.get("medication"),
        "dosage": prescription.get("dosage"),
        "risk_level": "high" if prescription.get("controlled", False) else "standard"
    },
    policy_id="policy_prescriptions_xyz123"  # Stricter policy for prescriptions
)
async def write_prescription(patient_id: str, prescription: dict) -> dict:
    """
    Write prescription for a patient (requires elevated privileges).
    
    Uses stricter policy than standard record access.
    Requires 'roots' capability AND specific agent approval.
    High-risk controlled substances may be denied by policy.
    
    Args:
        patient_id: Unique patient identifier
        prescription: Dict with medication, dosage, frequency, controlled flag
        
    Returns:
        Prescription confirmation with verification requirements
    """
    logger.info(f"Writing prescription for patient: {patient_id}")
    
    # Get agent info for audit trail
    agent_info = await get_agent_info()
    
    # Check if this is a controlled substance
    is_controlled = prescription.get("controlled", False)
    
    return {
        "status": "prescribed",
        "patient_id": patient_id,
        "prescription": prescription,
        "prescription_id": f"RX-{patient_id}-{prescription['medication'][:3].upper()}",
        "prescribing_agent": agent_info.get("agent_name"),
        "timestamp": "2024-10-30T12:00:00Z",
        "requires_pharmacist_verification": is_controlled,
        "notes": "DEA verification required" if is_controlled else "Standard prescription"
    }


@mcp.tool()
@require_policy(
    lambda patient_id, data: {
        "patient_id": patient_id,
        "data_type": "lab_results",
        "urgency": "high" if data.get("abnormal", False) else "routine"
    }
)
async def upload_lab_results(patient_id: str, data: dict) -> dict:
    """
    Upload lab results for a patient.
    
    Requires 'roots' capability for filesystem access.
    High urgency results may trigger additional notifications.
    
    Args:
        patient_id: Unique patient identifier
        data: Lab results with test_name, values, abnormal flag
        
    Returns:
        Upload confirmation with result summary
    """
    logger.info(f"Uploading lab results for patient: {patient_id}")
    
    # Get agent info for audit trail
    agent_info = await get_agent_info()
    
    is_abnormal = data.get("abnormal", False)
    
    return {
        "status": "uploaded",
        "patient_id": patient_id,
        "test_type": data.get("test_name", "General Lab Panel"),
        "result_summary": data.get("values", {}),
        "abnormal_flag": is_abnormal,
        "uploaded_by": agent_info.get("agent_name"),
        "timestamp": "2024-10-30T12:00:00Z",
        "follow_up_required": is_abnormal,
        "notification_sent": "physician" if is_abnormal else "none"
    }


@mcp.tool()
async def get_agent_status() -> dict:
    """
    Get the current agent's registration status and capabilities.
    
    Shows agent identity and permissions in the healthcare system.
    
    Returns:
        A dictionary with agent information and access level
    """
    agent_info = await get_agent_info()
    
    return {
        # Agent identity (from Iron Book)
        "agent": {
            "name": agent_info.get("agent_name"),
            "version": agent_info.get("agent_version"),
            "did": agent_info["agent_did"],
            "developer_did": agent_info["developer_did"],
            "capabilities": agent_info["capabilities"],
            "description": f"Healthcare agent for {agent_info.get('agent_name')}"
        },
        
        # Healthcare-specific context
        "access_level": "Provider" if "roots" in agent_info["capabilities"] else "Read-only",
        "can_prescribe": "roots" in agent_info["capabilities"],
        "can_access_records": True,
        
        # Status
        "status": "registered",
        "identification_method": agent_info.get("identification_method", "user-agent"),
        "security": {
            "authorization": "Iron Book Policy Engine (HIPAA-compliant)",
            "audit_logging": "Enabled",
            "encryption": "TLS 1.3"
        }
    }


@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about this healthcare MCP server.
    
    Returns:
        A dictionary containing server metadata
    """
    return {
        "name": "Healthcare MCP Server",
        "version": "1.0.0",
        "description": "HIPAA-compliant medical record access with Iron Book security",
        "compliance": ["HIPAA", "SOC2"],
        "authentication": "Agent-based (Iron Book)",
        "authorization": "Policy-based access control",
        "security_features": [
            "Dynamic agent registration",
            "Role-based access control",
            "Complete audit logging",
            "Policy-based authorization",
            "Trust score tracking"
        ],
        "tools": [
            "get_patient_record",
            "write_prescription",
            "upload_lab_results",
            "get_agent_status",
            "get_server_info"
        ]
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()


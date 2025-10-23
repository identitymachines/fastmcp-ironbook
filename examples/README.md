# fastmcp-ironbook Examples

This directory contains complete, runnable examples demonstrating how to use `fastmcp-ironbook` in real-world scenarios.

## Available Examples

### 🏥 Healthcare Server

**Path**: `healthcare/`

A HIPAA-compliant medical record access server demonstrating:
- Patient record management
- Prescription writing with elevated privileges
- Lab result uploads
- Multi-tier policy enforcement
- Complete audit trails

**Use Case**: Shows how to implement enterprise-grade security for sensitive healthcare data with role-based access control and compliance requirements.

**[View Healthcare Example →](healthcare/README.md)**

---

## Coming Soon

We're working on additional examples to demonstrate other use cases:

- **Financial Services**: Transaction processing with fraud detection
- **Admin Tools**: System administration with privilege escalation
- **Multi-Tenant SaaS**: Isolated data access across organizations

## Contributing Examples

Have a great example to share? We'd love to include it!

1. Create a new directory under `examples/`
2. Include a complete README with setup instructions
3. Add policy files demonstrating security patterns
4. Ensure all sensitive data is mocked/anonymized
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Getting Started

Each example is self-contained with:
- Complete server implementation
- Policy files (`.rego`)
- Configuration examples
- Step-by-step README
- Requirements file

To run any example:

1. Navigate to the example directory
2. Follow the README instructions
3. Install dependencies
4. Configure Iron Book credentials
5. Run the server

## Questions?

- **Package Documentation**: [packages/fastmcp-ironbook/README.md](../packages/fastmcp-ironbook/README.md)
- **Issues**: [GitHub Issues](https://github.com/identitymachines/fastmcp-ironbook/issues)


# Contributing to fastmcp-ironbook

Thank you for your interest in contributing! This document provides guidelines for contributing to the `fastmcp-ironbook` project.

## Ways to Contribute

### 1. Report Bugs

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant code snippets or logs

### 2. Suggest Features

Have an idea? Open an issue with:
- Use case description
- Proposed solution
- Alternative approaches considered
- Example code (if applicable)

### 3. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or clarify explanations
- Add examples or use cases
- Improve code comments
- Translate documentation

### 4. Submit Code

See "Development Workflow" below.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Iron Book account (for testing)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/identitymachines/fastmcp-ironbook.git
cd fastmcp-ironbook

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
cd packages/fastmcp-ironbook
pip install -e ".[dev]"

# Return to root
cd ../..
```

### Environment Configuration

Create `.env` in the root directory:

```bash
# Iron Book credentials (for testing)
IRONBOOK_API_KEY=your_test_api_key
IRONBOOK_BASE_URL=https://api.ironbook.identitymachines.com
```

## Repository Structure

```
fastmcp-ironbook/
├── packages/
│   └── fastmcp-ironbook/      # Main package
│       ├── src/
│       │   └── fastmcp_ironbook/
│       │       ├── __init__.py
│       │       ├── decorator.py    # @require_policy decorator
│       │       ├── middleware.py   # ClientInfoMiddleware
│       │       ├── agent.py        # Agent registration
│       │       └── policy.py       # Policy enforcement
│       ├── pyproject.toml
│       └── README.md
├── examples/
│   ├── healthcare/            # Healthcare example
│   └── README.md
├── docs/                      # Documentation
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md            # This file
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

#### Package Changes

When modifying the package (`packages/fastmcp-ironbook/src/`):

1. Update code with clear comments
2. Maintain type hints
3. Follow existing code style
4. Update docstrings

#### Documentation Changes

When updating docs:

1. Use clear, concise language
2. Include code examples
3. Test all commands/code snippets
4. Update table of contents if needed

### 3. Test Your Changes

#### Manual Testing

Test with a local server:

```bash
# Create a test server
cat > test_server.py << 'EOF'
import os
from fastmcp import FastMCP
from ironbook_sdk import IronBookClient
import sys
sys.path.insert(0, 'packages/fastmcp-ironbook/src')
import fastmcp_ironbook
from fastmcp_ironbook import ClientInfoMiddleware, require_policy

mcp = FastMCP("test-server")
ironbook = IronBookClient(api_key=os.getenv("IRONBOOK_API_KEY"))
mcp_client_info_cache = {}
agent_registry = {}

mcp.add_middleware(ClientInfoMiddleware(mcp_client_info_cache))
fastmcp_ironbook.setup(
    mcp_server=mcp,
    ironbook_client=ironbook,
    client_info_cache=mcp_client_info_cache,
    agent_registry=agent_registry,
    default_policy_id="policy_test123"
)

@mcp.tool()
@require_policy()
async def test_tool(msg: str) -> str:
    return f"Received: {msg}"

if __name__ == "__main__":
    mcp.run()
EOF

# Run it
python test_server.py
```

#### Integration Testing

Test with Cursor or Claude Desktop:

1. Configure `.cursor/mcp.json` to use your local version
2. Test all affected functionality
3. Verify audit logs in Iron Book Console

### 4. Commit Your Changes

Follow conventional commit format:

```bash
# Features
git commit -m "feat: add support for custom policy context"

# Bug fixes
git commit -m "fix: resolve agent registration race condition"

# Documentation
git commit -m "docs: add healthcare example walkthrough"

# Refactoring
git commit -m "refactor: simplify policy enforcement logic"

# Tests
git commit -m "test: add integration tests for middleware"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Testing notes

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small

Example:

```python
async def enforce_policy(
    ironbook_client: IronBookClient,
    agent_info: dict,
    action: str,
    resource: str,
    context: Optional[dict] = None,
    policy_id: str = "default_policy"
) -> bool:
    """
    Enforce Iron Book policy before executing a tool.
    
    Args:
        ironbook_client: Iron Book SDK client instance
        agent_info: Agent information dict with DID and VC
        action: The action being performed
        resource: The resource being accessed
        context: Optional context for policy evaluation
        policy_id: Iron Book policy ID to evaluate
    
    Returns:
        True if allowed
        
    Raises:
        PermissionError: If policy denies access
    """
    # Implementation
```

### Documentation Style

- Use clear, active voice
- Include code examples
- Provide both simple and advanced examples
- Link to relevant resources

## Adding Examples

To add a new example:

1. Create directory: `examples/your-example/`
2. Include these files:
   - `README.md` - Complete setup and usage guide
   - `server.py` - The MCP server implementation
   - `policies/` - Policy files (`.rego`)
   - `requirements.txt` - Dependencies
   - `.env.example` - Environment template
   - `mcp-config.example.json` - MCP client config

3. Update `examples/README.md` to list your example
4. Test thoroughly
5. Use mock/anonymized data only

Example structure:

```
examples/your-example/
├── README.md
├── server.py
├── policies/
│   └── your-policy.rego
├── requirements.txt
├── .env.example
└── mcp-config.example.json
```

## Testing Guidelines

### Before Submitting

- [ ] Code runs without errors
- [ ] All existing examples still work
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive data in commits
- [ ] Changes work with latest FastMCP version

### Integration Testing Checklist

- [ ] Agent registration succeeds
- [ ] Policy enforcement works correctly
- [ ] Audit logs appear in Iron Book Console
- [ ] Error messages are clear and helpful
- [ ] Works with Cursor/Claude Desktop

## Package Release Process

(For maintainers)

1. Update version in `packages/fastmcp-ironbook/pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.x.x`
4. Build: `python -m build`
5. Publish: `twine upload dist/*`
6. Create GitHub release

## Questions?

- **General Questions**: Open a discussion on GitHub
- **Bug Reports**: Open an issue
- **Security Issues**: Email security@identitymachines.com
- **Package Support**: support@identitymachines.com

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

### Enforcement

Violations may result in temporary or permanent ban from the project.

Report issues to: conduct@identitymachines.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to fastmcp-ironbook! 🎉


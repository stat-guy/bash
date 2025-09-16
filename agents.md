# MCP Bash Server - Agent Implementation Guide

> **FOR AI AGENTS/LLMs ONLY** - This document contains instructions for AI assistants to implement the Advanced MCP Bash Server.

## Quick Implementation Protocol

### Step 1: Download and Install
```bash
# Clone repository
git clone https://github.com/stat-guy/bash.git
cd bash

# Install dependencies
npm install
pip3 install mcp pydantic

# Verify installation
npm test
```

### Step 2: Add to MCP Configuration
Add to your MCP server configuration (typically `~/.config/claude_desktop_config.json` or similar):
```json
{
  "mcpServers": {
    "bash": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/bash/mcp-bash-wrapper.js"]
    }
  }
}
```

**CRITICAL**: Replace `/ABSOLUTE/PATH/TO` with the actual absolute path to the cloned repository.

### Step 3: Available Tools
The server provides these MCP tools:

#### Core Execution
- `mcp__bash__execute_command(command, session_id="default", timeout=30, background=False)`
- `mcp__bash__list_sessions()`
- `mcp__bash__create_session(session_id, working_directory=None)`
- `mcp__bash__kill_session(session_id)`

#### File Operations
- `mcp__bash__upload_file(file_path, content, encoding="base64", session_id="default", mode="w")`
- `mcp__bash__download_file(file_path, encoding="base64", session_id="default", max_size=10485760)`

#### Server Management
- `mcp__bash__get_server_info()`

## Usage Patterns for Agents

### Basic Command Execution
```python
# Simple command
result = await mcp__bash__execute_command("ls -la")

# Command with timeout
result = await mcp__bash__execute_command("npm install", timeout=300)

# Background execution
result = await mcp__bash__execute_command("docker build .", background=True)
```

### Multi-Session Workflows
```python
# Create project sessions
await mcp__bash__create_session("frontend", "/path/to/frontend")
await mcp__bash__create_session("backend", "/path/to/backend")

# Execute in specific contexts  
await mcp__bash__execute_command("npm start", session_id="frontend")
await mcp__bash__execute_command("python manage.py runserver", session_id="backend")

# Clean up when done
await mcp__bash__kill_session("frontend")
await mcp__bash__kill_session("backend")
```

### File Management
```python
# Upload configuration file
await mcp__bash__upload_file("config.json", base64_content, encoding="base64")

# Download results
result = await mcp__bash__download_file("output.log", encoding="text")

# Upload script and execute
await mcp__bash__upload_file("deploy.sh", script_content, encoding="text")
await mcp__bash__execute_command("chmod +x deploy.sh && ./deploy.sh")
```

## Advanced Implementation Strategies

### Session Isolation Strategy
Use separate sessions for:
- Different projects/repositories
- Different development environments (dev/staging/prod)
- Long-running processes (servers, builds, tests)
- Different user contexts or permissions

### Error Handling Protocol
```python
try:
    result = await mcp__bash__execute_command(command, timeout=60)
    if "timeout" in result and result["timeout"]:
        # Handle timeout
        await mcp__bash__kill_session(session_id)  # Clean up if needed
        
    if "stderr" in result and result["stderr"]:
        # Parse error output for actionable information
        
except Exception as e:
    # Handle MCP communication errors
    # Retry with new session if needed
```

### Performance Optimization
- Use `background=True` for long-running commands
- Set appropriate timeouts based on expected command duration
- Create sessions with specific working directories to avoid `cd` commands
- Clean up sessions when workflows complete

### Security Considerations
- Validate commands before execution
- Use session isolation for untrusted operations
- Monitor session resource usage with `list_sessions()`
- Set reasonable timeout limits to prevent resource exhaustion

## Integration Examples

### Development Workflow Agent
```python
async def setup_development_environment(project_path: str):
    session_id = f"dev_{project_path.split('/')[-1]}"
    
    # Create isolated session
    await mcp__bash__create_session(session_id, project_path)
    
    # Setup environment
    await mcp__bash__execute_command("npm install", session_id=session_id, timeout=300)
    await mcp__bash__execute_command("pip install -r requirements.txt", session_id=session_id, timeout=120)
    
    # Start development server
    await mcp__bash__execute_command("npm run dev", session_id=session_id, background=True)
    
    return session_id
```

### Testing Agent
```python
async def run_test_suite(project_session: str):
    # Run tests with detailed output
    test_result = await mcp__bash__execute_command(
        "npm test -- --coverage --verbose", 
        session_id=project_session,
        timeout=600
    )
    
    # Save test results
    await mcp__bash__upload_file(
        "test-results.json", 
        test_result["stdout"], 
        encoding="text",
        session_id=project_session
    )
    
    return test_result
```

### Deployment Agent
```python
async def deploy_application(build_session: str, target_env: str):
    # Build application
    build_result = await mcp__bash__execute_command(
        "npm run build:production", 
        session_id=build_session,
        timeout=900
    )
    
    if build_result["completed"]:
        # Deploy to target
        deploy_result = await mcp__bash__execute_command(
            f"./deploy.sh {target_env}", 
            session_id=build_session,
            timeout=300
        )
        return deploy_result
    else:
        raise Exception(f"Build failed: {build_result['stderr']}")
```

## Troubleshooting for Agents

### Common Issues and Solutions

**Tool not available**:
- Verify MCP server is properly configured
- Check absolute paths in configuration
- Restart the host application (Claude Desktop, etc.)

**Command timeouts**:
- Increase timeout parameter for long-running commands
- Use `background=True` for indefinite processes
- Split complex commands into smaller steps

**Session management**:
- Use `list_sessions()` to monitor active sessions
- Always clean up sessions after use
- Create new sessions if existing ones become unresponsive

**Permission errors**:
- Ensure proper file/directory permissions
- Use appropriate working directories
- Consider using `sudo` if elevation is required

### Best Practices Summary
1. **Always use absolute paths** in configuration
2. **Create isolated sessions** for different tasks
3. **Set appropriate timeouts** based on command complexity
4. **Clean up sessions** when workflows complete
5. **Handle errors gracefully** with proper exception handling
6. **Use background execution** for long-running processes
7. **Monitor session health** with regular status checks

---

**This server provides superior bash execution capabilities compared to standard MCP implementations. Use it to enhance your bash workflows with multi-session management and advanced process control.**
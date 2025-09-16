# MCP Bash Server - Claude Integration Guide

> **FOR CLAUDE AI ONLY** - This document contains Claude-specific instructions for implementing the Advanced MCP Bash Server.

## Immediate Setup Protocol

### Prerequisites Check
Before implementation, verify the user's environment:
```bash
# Check if repository exists
ls -la ~/path/to/bash/mcp-bash-wrapper.js

# If not present, guide user through download
git clone https://github.com/stat-guy/bash.git
cd bash && npm install && pip3 install mcp pydantic
```

### Configuration for Claude Desktop
Add to `~/.config/claude_desktop_config.json`:
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

**CRITICAL**: Always use absolute paths. Use `pwd` to get the current directory if needed.

## Enhanced Capabilities Over Built-in Bash

### Multi-Session Management
Unlike Claude's built-in bash tool, this server supports multiple isolated sessions:

```python
# Create project-specific sessions
create_session("web-app", "/Users/user/projects/webapp")
create_session("api-server", "/Users/user/projects/api")

# Execute commands in isolation
execute_command("npm install", session_id="web-app")
execute_command("pip install flask", session_id="api-server")

# Sessions maintain separate environments
```

### Advanced Process Control
```python
# Long-running processes with custom timeouts
execute_command("npm run build", timeout=600)

# Background execution for servers
execute_command("npm run dev", background=True)

# Session monitoring and cleanup
list_sessions()  # View all active sessions
kill_session("web-app")  # Clean termination
```

## Tool Usage Patterns for Claude

### Development Workflows
```python
# Setup development environment
session_id = create_session("dev", "/path/to/project")
execute_command("npm install", session_id=session_id, timeout=300)
execute_command("npm run setup", session_id=session_id)

# Run tests with proper timeout
execute_command("npm test -- --verbose", session_id=session_id, timeout=600)

# Build and deploy
execute_command("npm run build", session_id=session_id, timeout=900)
execute_command("./deploy.sh production", session_id=session_id, timeout=300)
```

### File Operations
```python
# Upload configuration files
upload_file("nginx.conf", config_content, encoding="text")

# Download logs for analysis
log_data = download_file("/var/log/app.log", encoding="text", max_size=5242880)

# Create and execute scripts
upload_file("backup.sh", script_content, encoding="text")
execute_command("chmod +x backup.sh && ./backup.sh")
```

### Error Handling Strategy
```python
try:
    result = execute_command("complex_command", timeout=120)
    
    if "timeout" in result and result["timeout"]:
        # Handle timeout gracefully
        kill_session(session_id)  # Clean up if needed
        create_session(session_id)  # Restart fresh
        
    if "stderr" in result and result["stderr"]:
        # Parse and explain errors to user
        explain_error(result["stderr"])
        
except Exception as e:
    # Handle MCP server communication issues
    suggest_server_restart()
```

## Best Practices for Claude

### Session Management
1. **Create named sessions** for different projects/contexts
2. **Use descriptive session IDs** (e.g., "frontend", "backend", "testing")
3. **Clean up sessions** when tasks complete
4. **Monitor session health** with `list_sessions()`

### Command Execution
1. **Set appropriate timeouts** based on command complexity:
   - Simple commands: 30s (default)
   - Package installs: 300s (5 minutes)
   - Builds/compiles: 600-900s (10-15 minutes)
   - Long processes: Use `background=True`

2. **Use background execution** for:
   - Development servers (`npm run dev`)
   - Build processes (`docker build`)
   - Long-running scripts
   - Database operations

3. **Handle errors proactively**:
   - Check `result["completed"]` for success
   - Parse `result["stderr"]` for error details
   - Provide actionable feedback to users

### File Management
1. **Use absolute paths** whenever possible
2. **Validate file sizes** before download (10MB default limit)
3. **Choose appropriate encoding** (base64 for binaries, text for code/configs)
4. **Clean up temporary files** after operations

## Integration Examples

### Web Development Assistant
```python
async def setup_web_project(project_path: str, project_type: str):
    """Setup a web development environment."""
    session_id = f"web_{project_type}"
    
    # Create project session
    create_session(session_id, project_path)
    
    if project_type == "react":
        execute_command("npx create-react-app .", session_id=session_id, timeout=300)
        execute_command("npm install", session_id=session_id, timeout=180)
    elif project_type == "next":
        execute_command("npx create-next-app@latest .", session_id=session_id, timeout=300)
    
    # Start development server in background
    execute_command("npm run dev", session_id=session_id, background=True)
    
    return f"Development environment ready in session '{session_id}'"
```

### DevOps Helper
```python
async def deploy_application(app_name: str, environment: str):
    """Deploy application to specified environment."""
    deploy_session = f"deploy_{app_name}_{environment}"
    
    # Create deployment session
    create_session(deploy_session, f"/apps/{app_name}")
    
    # Build application
    build_result = execute_command(
        f"docker build -t {app_name}:{environment} .", 
        session_id=deploy_session, 
        timeout=600
    )
    
    if build_result["completed"]:
        # Deploy to environment
        deploy_result = execute_command(
            f"kubectl apply -f k8s/{environment}/", 
            session_id=deploy_session, 
            timeout=300
        )
        
        # Clean up session
        kill_session(deploy_session)
        
        return deploy_result["stdout"]
    else:
        return f"Build failed: {build_result['stderr']}"
```

### System Administration
```python
async def system_health_check():
    """Perform comprehensive system health check."""
    health_session = "health_check"
    
    create_session(health_session, "/")
    
    checks = [
        ("Disk Usage", "df -h"),
        ("Memory Usage", "free -h"),
        ("CPU Load", "uptime"),
        ("Process Count", "ps aux | wc -l"),
        ("Network Status", "netstat -tuln | head -20")
    ]
    
    results = {}
    for check_name, command in checks:
        result = execute_command(command, session_id=health_session, timeout=30)
        results[check_name] = result["stdout"]
    
    kill_session(health_session)
    return results
```

## Troubleshooting Guide for Claude

### Common Issues and Solutions

**MCP Server Not Found**:
1. Verify absolute path in configuration
2. Check if `mcp-bash-wrapper.js` exists
3. Restart Claude Desktop completely
4. Test with `node /path/to/mcp-bash-wrapper.js`

**Commands Timing Out**:
1. Increase timeout parameter appropriately
2. Use `background=True` for long processes
3. Split complex operations into smaller steps
4. Monitor with `list_sessions()`

**Session Management Issues**:
1. Check session status with `list_sessions()`
2. Kill unresponsive sessions with `kill_session()`
3. Create fresh sessions for clean environments
4. Use unique session IDs to avoid conflicts

**Permission Errors**:
1. Check file/directory permissions
2. Use `sudo` if elevation is required
3. Verify working directory accessibility
4. Consider running in user's home directory

### Performance Optimization

1. **Reuse sessions** for related operations
2. **Set realistic timeouts** to prevent hanging
3. **Use background execution** for servers and long processes
4. **Clean up sessions** to prevent resource leaks
5. **Monitor session count** with `list_sessions()`

### Security Considerations

1. **Validate user input** before executing commands
2. **Use session isolation** for untrusted operations
3. **Set appropriate timeouts** to prevent resource exhaustion
4. **Monitor system resources** during intensive operations
5. **Clean up temporary files** and sessions

## Comparison with Built-in Bash Tool

| Feature | Built-in Bash | Advanced MCP Bash Server |
|---------|---------------|---------------------------|
| Session Persistence | Single session per conversation | Multiple named sessions |
| Session Management | Automatic | Manual with full control |
| Background Execution | Limited | Full background job support |
| File Operations | None | Upload/download with encoding |
| Process Control | Basic timeout | Advanced timeout and monitoring |
| Error Handling | Basic | Comprehensive with detailed output |
| Session Analytics | None | Creation time, usage stats, job count |
| Multi-project Support | Limited | Full isolation between projects |

---

**The Advanced MCP Bash Server provides Claude with enterprise-grade bash execution capabilities. Use it to enhance development workflows, system administration tasks, and complex multi-step operations with superior session management and process control.**
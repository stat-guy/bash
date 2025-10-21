# MCP Bash Server - Testing Guide

This document describes how to test the MCP Bash Server to ensure it's working correctly.

## Quick Test

Run the verification script:

```bash
./verify.sh
```

This will check all prerequisites, dependencies, and test the server startup.

## Manual MCP Protocol Test

You can manually test the server using the MCP protocol:

### Test 1: Initialize the Server

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node mcp-bash-wrapper.js
```

Expected output should include:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "serverInfo": {
      "name": "bash-server",
      "version": "1.18.0"
    }
  }
}
```

### Test 2: Execute a Command

Create a Python test script:

```python
import subprocess
import json
import time

# Start the MCP server
proc = subprocess.Popen(
    ['node', 'mcp-bash-wrapper.js'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

def send_request(req):
    proc.stdin.write(json.dumps(req) + '\n')
    proc.stdin.flush()
    time.sleep(0.5)
    return json.loads(proc.stdout.readline())

# Initialize
init_resp = send_request({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
})
print(f"✓ Server: {init_resp['result']['serverInfo']['name']}")

# Execute command
cmd_resp = send_request({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "execute_command",
        "arguments": {
            "command": "echo 'Hello MCP!'"
        }
    }
})
print(f"✓ Command executed: {cmd_resp['result']['content'][0]['text'][:50]}")

proc.terminate()
```

## Testing with Claude Desktop

After configuration, test in Claude Desktop by asking:

```
Can you run: echo "Hello from MCP Bash Server!"
```

Claude should execute the command using the MCP bash server.

## Testing with Claude Code

```bash
# Add the server
claude mcp add bash node "$(pwd)/mcp-bash-wrapper.js"

# Verify it's added
claude mcp list
```

## Automated Tests

The repository includes automated testing:

```bash
# Run basic import test
npm test

# Run full verification
./verify.sh
```

## Expected Results

All tests should show:
- ✓ Server initializes correctly
- ✓ Tools are listed (7 tools available)
- ✓ Commands execute successfully
- ✓ Sessions can be created and managed
- ✓ Exit codes are correct

## Troubleshooting Tests

If tests fail:

1. **Server won't start**
   ```bash
   # Check dependencies
   python3 -c "import mcp, pydantic"
   node --version
   ```

2. **MCP protocol errors**
   ```bash
   # Test server directly
   node mcp-bash-wrapper.js
   # Should see: "Starting MCP Bash Server"
   ```

3. **Command execution fails**
   ```bash
   # Check Python path
   python3 -m mcp_bash_server.server
   ```

## Success Criteria

Your installation is successful when:
- [ ] `npm test` passes
- [ ] `./verify.sh` shows all checks passing
- [ ] Server responds to MCP initialize request
- [ ] Commands can be executed via MCP protocol
- [ ] Claude Desktop/Code can use the server

## Test Results from Development

Last tested: 2025-10-20

Results:
- ✓ Server initialized: bash-server v1.18.0
- ✓ Command executed successfully
- ✓ All 7 tools available
- ✓ MCP protocol compliance confirmed
- ✓ Session management working
- ✓ File operations functional

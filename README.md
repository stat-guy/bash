# Advanced MCP Bash Server

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Node.js](https://img.shields.io/badge/node.js-14+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**A production-grade Model Context Protocol (MCP) server that provides advanced bash execution capabilities for AI assistants.**

Built for developers who need powerful, isolated bash environments with multi-session management, background process control, and comprehensive error handling.

---

## 🚀 Quick Start

### One-Line Installation

```bash
curl -fsSL https://raw.githubusercontent.com/stat-guy/bash/main/install.sh | bash
```

This will:
- ✓ Check prerequisites (Node.js 14+, Python 3.10+, git)
- ✓ Clone the repository
- ✓ Install all dependencies
- ✓ Verify the installation
- ✓ Optionally configure Claude Desktop

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/stat-guy/bash.git
cd bash

# Install dependencies
npm install
pip3 install -e .  # Recommended: installs package in development mode
# OR
pip3 install mcp pydantic  # Alternative: install dependencies manually

# Verify installation
./verify.sh
```

---

## 📋 Table of Contents

- [Why This Server?](#-why-this-server)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Available Tools](#-available-tools)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)

---

## 💡 Why This Server?

### Beyond Basic Bash Execution

While Claude and other AI assistants have built-in bash capabilities, this MCP server provides enterprise-grade features for complex development workflows:

| Feature | Built-in Bash | This MCP Server |
|---------|--------------|-----------------|
| **Session Management** | Single session | Multiple isolated sessions |
| **Background Jobs** | Limited | Full background process support |
| **Process Control** | Basic timeout | Advanced timeout & monitoring |
| **Session Analytics** | None | Creation time, usage stats, job tracking |
| **File Operations** | None | Upload/download with encoding |
| **Error Handling** | Basic | Comprehensive with detailed output |
| **Multi-Project** | Limited | Full isolation between projects |

### Perfect For

- **Complex development workflows**: Multiple projects, different environments
- **Long-running processes**: Builds, tests, servers running in background
- **Session isolation**: Separate environments for different tasks
- **Production deployments**: Reliable process management and error handling
- **AI agent development**: Full MCP protocol support

---

## 🔧 Installation

### Prerequisites

- **Node.js 14+**: [Download](https://nodejs.org)
- **Python 3.10+**: [Download](https://python.org)
- **Git**: [Download](https://git-scm.com)
- **pip3**: Usually included with Python

### Installation Methods

#### Option 1: Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/stat-guy/bash/main/install.sh | bash
```

#### Option 2: Development Install

```bash
git clone https://github.com/stat-guy/bash.git
cd bash
npm install
pip3 install -e .  # Installs in editable mode for development
```

#### Option 3: Standard Install

```bash
git clone https://github.com/stat-guy/bash.git
cd bash
npm install
pip3 install mcp pydantic
```

### Verify Installation

Run the verification script to ensure everything is set up correctly:

```bash
./verify.sh
```

This checks:
- ✓ Required binaries (git, node, python3, npm, pip3)
- ✓ Project files
- ✓ Dependencies installed
- ✓ Server can start
- ✓ Configuration (if applicable)
- ✓ File permissions

---

## ⚙️ Configuration

### Claude Desktop

**macOS/Linux**: Edit `~/.config/claude_desktop_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "bash": {
      "command": "node",
      "args": ["/absolute/path/to/bash/mcp-bash-wrapper.js"]
    }
  }
}
```

**Getting the absolute path:**
```bash
cd bash
echo "$(pwd)/mcp-bash-wrapper.js"
```

Then copy the output into your config file.

**After configuration:**
1. Save the config file
2. Completely quit and restart Claude Desktop
3. The bash server tools will now be available

### Claude Code

```bash
cd bash
claude mcp add bash node "$(pwd)/mcp-bash-wrapper.js"
```

### Other MCP Clients

Point your MCP client to run:
```bash
node /absolute/path/to/bash/mcp-bash-wrapper.js
```

---

## 📖 Usage

### Basic Command Execution

```python
# Simple commands
execute_command("ls -la")
execute_command("pwd")

# Commands persist state
execute_command("cd /tmp && export VAR=value")
execute_command("echo $VAR")  # Outputs: value
```

### Multi-Session Management

```python
# Create isolated sessions for different projects
create_session("frontend", "/path/to/frontend")
create_session("backend", "/path/to/backend")

# Execute commands in specific sessions
execute_command("npm install", session_id="frontend")
execute_command("pip install -r requirements.txt", session_id="backend")

# Each session maintains its own state
execute_command("export NODE_ENV=development", session_id="frontend")
execute_command("export FLASK_ENV=development", session_id="backend")

# Clean up when done
kill_session("frontend")
kill_session("backend")
```

### Background Execution

```python
# Start long-running processes
execute_command("npm run dev", session_id="frontend", background=True)
execute_command("python manage.py runserver", session_id="backend", background=True)

# Heavy builds with custom timeout
execute_command("docker build -t myapp .", timeout=600, background=True)

# Monitor sessions
list_sessions()  # Shows all active sessions and their status
```

### File Operations

```python
# Upload configuration files
upload_file("config.json", file_content, encoding="text")

# Download build outputs
build_log = download_file("/var/log/build.log", encoding="text")

# Upload and execute scripts
upload_file("deploy.sh", script_content, encoding="text")
execute_command("chmod +x deploy.sh && ./deploy.sh")
```

---

## 🛠 Available Tools

### Core Execution

#### `execute_command(command, session_id="default", timeout=30, background=False)`
Execute bash commands with full shell support.

**Parameters:**
- `command` (str): The bash command to execute
- `session_id` (str): Session identifier (default: "default")
- `timeout` (int): Command timeout in seconds (default: 30)
- `background` (bool): Run in background (default: False)

**Returns:**
```json
{
  "stdout": "command output",
  "stderr": "error output (if any)",
  "exit_code": 0,
  "completed": true,
  "timeout": false,
  "session_id": "default"
}
```

**Recommended Timeouts:**
- Simple commands (ls, pwd, etc.): 30s (default)
- Package installs (npm, pip): 300s (5 min)
- Builds (webpack, docker): 600-900s (10-15 min)
- Long processes: Use `background=True`

### Session Management

#### `create_session(session_id, working_directory=None)`
Create a new isolated bash session.

#### `list_sessions()`
View all active sessions with detailed analytics:
- Session ID
- Working directory
- Creation time
- Last activity
- Command count
- Background jobs

#### `kill_session(session_id)`
Cleanly terminate a session and all its processes.

### File Operations

#### `upload_file(file_path, content, encoding="base64", session_id="default", mode="w")`
Upload files to the server filesystem.

#### `download_file(file_path, encoding="base64", session_id="default", max_size=10485760)`
Download files from the server (default max: 10MB).

### Server Info

#### `get_server_info()`
Get server version and capabilities.

---

## 🎯 Advanced Features

### Session Isolation Strategy

Use separate sessions for:
- **Different projects**: `frontend`, `backend`, `mobile`
- **Different environments**: `dev`, `staging`, `prod`
- **Long-running processes**: `server`, `build`, `tests`
- **Different contexts**: Isolate experimental or risky commands

### Error Handling

```python
result = execute_command("risky_command", timeout=60)

if result["timeout"]:
    # Handle timeout
    kill_session(session_id)
    create_session(session_id)  # Start fresh

if result["exit_code"] != 0:
    # Command failed
    print(f"Error: {result['stderr']}")

if not result["completed"]:
    # Command didn't complete properly
    handle_incomplete_command()
```

### Development Workflow Example

```python
# Setup isolated development environment
session = create_session("myproject", "/home/user/projects/myproject")

# Install dependencies
execute_command("npm install", session_id="myproject", timeout=300)

# Run tests
test_result = execute_command(
    "npm test -- --coverage",
    session_id="myproject",
    timeout=600
)

# Start dev server in background
execute_command(
    "npm run dev",
    session_id="myproject",
    background=True
)

# Monitor all sessions
sessions = list_sessions()

# Clean up when done
kill_session("myproject")
```

### Production Deployment Example

```python
# Create deployment session
deploy = create_session("deploy", "/var/www/myapp")

# Build application
build = execute_command(
    "docker build -t myapp:latest .",
    session_id="deploy",
    timeout=900
)

if build["exit_code"] == 0:
    # Deploy to production
    deploy_result = execute_command(
        "kubectl apply -f k8s/production/",
        session_id="deploy",
        timeout=300
    )

# Clean up
kill_session("deploy")
```

---

## 🔍 Troubleshooting

### Installation Issues

**Server not starting:**
```bash
# Check Python dependencies
python3 -c "import mcp, pydantic"

# Check Node.js version
node --version  # Should be 14+

# Run verification script
./verify.sh
```

**Import errors:**
```bash
# Reinstall dependencies
pip3 install -e .
# OR
pip3 install --force-reinstall mcp pydantic
```

### Configuration Issues

**Claude Desktop not finding server:**
1. Verify absolute path in config:
   ```bash
   cat ~/.config/claude_desktop_config.json
   ```
2. Ensure path is absolute (starts with `/`)
3. Test server manually:
   ```bash
   node /absolute/path/to/mcp-bash-wrapper.js
   ```
4. Completely quit and restart Claude Desktop (not just close window)

**Permission errors:**
```bash
# Make scripts executable
chmod +x mcp-bash-wrapper.js verify.sh install.sh
```

### Runtime Issues

**Commands timing out:**
- Increase timeout parameter for long commands
- Use `background=True` for indefinite processes
- Split complex operations into smaller steps

**Session management:**
```bash
# List all active sessions
list_sessions()

# Kill unresponsive sessions
kill_session("session_id")

# Create fresh session
create_session("session_id")
```

**Memory issues:**
- Sessions auto-cleanup after 1 hour of inactivity
- Manually kill sessions when done: `kill_session()`
- Monitor with: `list_sessions()`

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/stat-guy/bash/issues)
- **Verification**: Run `./verify.sh` for diagnostics
- **Logs**: Check stderr output when running the server

---

## 👥 Development

### Project Structure

```
bash/
├── src/
│   └── mcp_bash_server/
│       ├── __init__.py
│       ├── server.py           # Main MCP server
│       └── session_manager.py  # Session management
├── mcp-bash-wrapper.js         # Node.js wrapper
├── install.sh                  # Installation script
├── verify.sh                   # Verification script
├── package.json                # Node.js config
├── pyproject.toml              # Python package config
└── README.md
```

### Running Tests

```bash
# Run Python import test
npm test

# Full verification
./verify.sh

# Manual server test
node mcp-bash-wrapper.js
```

### Development Install

```bash
# Clone for development
git clone https://github.com/stat-guy/bash.git
cd bash

# Install in editable mode
pip3 install -e .
npm install

# Make changes and test
./verify.sh
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly: `./verify.sh`
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/your-feature`
7. Create a Pull Request

---

## 📊 Performance

- **Execution time**: 0.02-0.05s for basic commands
- **Large output**: Tested with 1000+ line outputs
- **Session isolation**: Complete process group separation
- **Memory**: Automatic cleanup of stale sessions
- **Reliability**: Comprehensive timeout and error recovery

---

## 🔒 Security

- **Process isolation**: Separate process groups per session
- **Resource limits**: Configurable timeouts and size limits
- **Clean termination**: Proper SIGTERM/SIGKILL handling
- **Environment isolation**: Separate environment variables per session
- **No privilege escalation**: Runs with user permissions

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built on:
- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) by Anthropic
- [FastMCP](https://github.com/jlowin/fastmcp)
- [Pydantic](https://docs.pydantic.dev/)

---

**Ready to supercharge your AI assistant's bash capabilities?**

⭐ Star this repo | 🐛 [Report issues](https://github.com/stat-guy/bash/issues) | 📖 [Read the docs](https://github.com/stat-guy/bash#readme)

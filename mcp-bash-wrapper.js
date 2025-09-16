#!/usr/bin/env node
/**
 * Node.js wrapper for MCP Bash Server
 * This allows the Python-based MCP server to be launched via 'node' command
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get the directory where this script is located
const scriptDir = __dirname;
const pythonServerPath = path.join(scriptDir, 'src', 'mcp_bash_server', 'server.py');

// Check if Python dependencies are installed
function checkDependencies() {
  try {
    execSync('python3 -c "import mcp, pydantic"', { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
}

// Install Python dependencies
function installDependencies() {
  console.error('Installing Python dependencies...');
  try {
    execSync('pip3 install mcp pydantic', { stdio: 'inherit' });
    console.error('Dependencies installed successfully');
    return true;
  } catch (error) {
    console.error('Failed to install dependencies:', error.message);
    console.error('Please run: pip3 install mcp pydantic');
    return false;
  }
}

// Check dependencies and install if needed
if (!checkDependencies()) {
  if (!installDependencies()) {
    process.exit(1);
  }
}

// Verify server file exists
if (!fs.existsSync(pythonServerPath)) {
  console.error('MCP Bash Server not found at:', pythonServerPath);
  process.exit(1);
}

// Set up environment
const env = {
  ...process.env,
  PYTHONPATH: path.join(scriptDir, 'src')
};

// Spawn the Python server
const python = spawn('python3', [pythonServerPath], {
  env: env,
  stdio: 'inherit',
  cwd: scriptDir
});

// Handle process events
python.on('error', (err) => {
  console.error('Failed to start MCP Bash Server:', err.message);
  process.exit(1);
});

python.on('close', (code) => {
  process.exit(code);
});

// Handle signals
process.on('SIGINT', () => {
  python.kill('SIGINT');
});

process.on('SIGTERM', () => {
  python.kill('SIGTERM');
});
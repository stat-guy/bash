#!/usr/bin/env bash
# Advanced MCP Bash Server - Quick Install Script
# Usage: curl -fsSL https://raw.githubusercontent.com/stat-guy/bash/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    local missing_deps=()

    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi

    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    else
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -lt 14 ]; then
            print_error "Node.js version 14+ required (found: $(node --version))"
            exit 1
        fi
    fi

    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
            print_error "Python 3.10+ required (found: $(python3 --version))"
            exit 1
        fi
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  macOS: brew install ${missing_deps[*]}"
        echo "  Linux: apt-get install ${missing_deps[*]} (or your package manager)"
        exit 1
    fi

    print_success "All prerequisites found"
}

# Determine installation directory
determine_install_dir() {
    if [ -d "bash" ] && [ -f "bash/mcp-bash-wrapper.js" ]; then
        print_warning "Found existing 'bash' directory"
        read -p "Use existing directory? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            INSTALL_DIR="$(cd bash && pwd)"
            print_info "Using existing directory: $INSTALL_DIR"
            return
        fi
    fi

    # Default to current directory + bash
    INSTALL_DIR="$(pwd)/bash"
}

# Clone or update repository
setup_repository() {
    print_info "Setting up repository..."

    if [ -d "$INSTALL_DIR/.git" ]; then
        print_info "Updating existing repository..."
        cd "$INSTALL_DIR"
        git pull origin main || print_warning "Could not update repository"
    else
        print_info "Cloning repository..."
        git clone https://github.com/stat-guy/bash.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi

    print_success "Repository ready"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."

    # Node.js dependencies
    if [ -f "package.json" ]; then
        print_info "Installing Node.js dependencies..."
        npm install --silent
        print_success "Node.js dependencies installed"
    fi

    # Python dependencies - offer both methods
    print_info "Installing Python dependencies..."

    # Try pip install first (cleaner)
    if pip3 install -e . &> /dev/null; then
        print_success "Python package installed in development mode"
    else
        # Fallback to manual install
        print_warning "Package install failed, installing dependencies manually..."
        pip3 install mcp pydantic
        print_success "Python dependencies installed"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    if npm test &> /dev/null; then
        print_success "Server verification passed"
    else
        print_error "Server verification failed"
        print_info "Run './verify.sh' for detailed diagnostics"
        return 1
    fi
}

# Configure MCP server
configure_mcp() {
    print_info "Configuring MCP server..."

    local config_file=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        config_file="$HOME/.config/claude_desktop_config.json"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        config_file="$HOME/.config/claude_desktop_config.json"
    else
        print_warning "Unsupported OS for auto-configuration"
        return
    fi

    local wrapper_path="$INSTALL_DIR/mcp-bash-wrapper.js"

    print_info "Add this to your Claude Desktop config ($config_file):"
    echo ""
    echo -e "${BLUE}{"
    echo "  \"mcpServers\": {"
    echo "    \"bash\": {"
    echo "      \"command\": \"node\","
    echo "      \"args\": [\"$wrapper_path\"]"
    echo "    }"
    echo "  }"
    echo -e "}${NC}"
    echo ""

    read -p "Automatically add to config? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$(dirname "$config_file")"

        if [ -f "$config_file" ]; then
            # Backup existing config
            cp "$config_file" "${config_file}.backup"
            print_success "Backed up existing config to ${config_file}.backup"
        fi

        # Create or update config
        cat > "$config_file" <<EOF
{
  "mcpServers": {
    "bash": {
      "command": "node",
      "args": ["$wrapper_path"]
    }
  }
}
EOF
        print_success "Configuration written to $config_file"
        print_warning "Please restart Claude Desktop to load the new server"
    else
        print_info "Manual configuration required"
    fi
}

# Alternative: Claude Code configuration
configure_claude_code() {
    echo ""
    print_info "For Claude Code users, run:"
    echo ""
    echo -e "${BLUE}claude mcp add bash node \"$INSTALL_DIR/mcp-bash-wrapper.js\"${NC}"
    echo ""
}

# Main installation flow
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║        Advanced MCP Bash Server - Installation          ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_prerequisites
    determine_install_dir
    setup_repository
    install_dependencies

    if verify_installation; then
        print_success "Installation complete!"
        echo ""
        configure_mcp
        configure_claude_code
        echo ""
        print_success "All done! 🚀"
        echo ""
        print_info "Next steps:"
        echo "  1. Restart Claude Desktop (if configured)"
        echo "  2. Run './verify.sh' to test the server"
        echo "  3. Check README.md for usage examples"
    else
        print_error "Installation completed with errors"
        print_info "Run './verify.sh' for troubleshooting"
        exit 1
    fi
}

main

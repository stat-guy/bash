#!/usr/bin/env bash
# Advanced MCP Bash Server - Verification Script
# Tests installation and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_test() {
    echo -e "\n${BLUE}▶${NC} Testing: $1"
}

print_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Test 1: Check required binaries
test_binaries() {
    print_test "System prerequisites"

    if command -v git &> /dev/null; then
        print_pass "git: $(git --version | head -n1)"
    else
        print_fail "git: not found"
    fi

    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        NODE_NUM=$(echo $NODE_VER | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_NUM" -ge 14 ]; then
            print_pass "node: $NODE_VER"
        else
            print_fail "node: $NODE_VER (need 14+)"
        fi
    else
        print_fail "node: not found"
    fi

    if command -v python3 &> /dev/null; then
        PY_VER=$(python3 --version)
        print_pass "python3: $PY_VER"
    else
        print_fail "python3: not found"
    fi

    if command -v npm &> /dev/null; then
        print_pass "npm: $(npm --version)"
    else
        print_fail "npm: not found"
    fi

    if command -v pip3 &> /dev/null; then
        print_pass "pip3: $(pip3 --version | cut -d' ' -f1-2)"
    else
        print_fail "pip3: not found"
    fi
}

# Test 2: Check project files
test_project_files() {
    print_test "Project files"

    local required_files=(
        "mcp-bash-wrapper.js"
        "package.json"
        "pyproject.toml"
        "src/mcp_bash_server/server.py"
        "src/mcp_bash_server/session_manager.py"
    )

    for file in "${required_files[@]}"; do
        if [ -f "$SCRIPT_DIR/$file" ]; then
            print_pass "$file"
        else
            print_fail "$file: missing"
        fi
    done
}

# Test 3: Check Node.js dependencies
test_node_deps() {
    print_test "Node.js dependencies"

    cd "$SCRIPT_DIR"

    if [ ! -d "node_modules" ]; then
        print_fail "node_modules: not found (run: npm install)"
        return
    fi

    print_pass "node_modules directory exists"

    # Check package.json dependencies
    if [ -f "package.json" ]; then
        print_pass "package.json found"
    fi
}

# Test 4: Check Python dependencies
test_python_deps() {
    print_test "Python dependencies"

    local required_modules=("mcp" "pydantic")

    for module in "${required_modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            local version=$(python3 -c "import $module; print(getattr($module, '__version__', 'unknown'))" 2>/dev/null)
            print_pass "$module: $version"
        else
            print_fail "$module: not installed"
        fi
    done
}

# Test 5: Test server startup
test_server_startup() {
    print_test "Server startup"

    cd "$SCRIPT_DIR"

    # Test import
    if python3 -c 'import sys; sys.path.insert(0, "src"); from mcp_bash_server.server import main' 2>/dev/null; then
        print_pass "Python imports successful"
    else
        print_fail "Python imports failed"
        return
    fi

    # Test npm test command
    if npm test &> /dev/null; then
        print_pass "npm test passed"
    else
        print_fail "npm test failed"
        print_info "Try running: npm test (to see errors)"
        return
    fi

    # Test actual server startup (with timeout)
    print_info "Testing server startup (3 second timeout)..."
    if timeout 3 node "$SCRIPT_DIR/mcp-bash-wrapper.js" 2>&1 | grep -q "Starting MCP Bash Server"; then
        print_pass "Server starts successfully"
    else
        print_warn "Could not verify server startup message"
    fi
}

# Test 6: Check MCP configuration
test_mcp_config() {
    print_test "MCP Configuration"

    local config_file=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        config_file="$HOME/.config/claude_desktop_config.json"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        config_file="$HOME/.config/claude_desktop_config.json"
    fi

    if [ -z "$config_file" ]; then
        print_warn "Unsupported OS for config check"
        return
    fi

    if [ ! -f "$config_file" ]; then
        print_warn "Claude Desktop config not found: $config_file"
        print_info "Config will be needed for Claude Desktop integration"
        return
    fi

    print_pass "Config file exists: $config_file"

    # Check if bash server is configured
    if grep -q "bash" "$config_file" 2>/dev/null; then
        print_pass "bash server configured in Claude Desktop"

        # Check if path matches current installation
        if grep -q "$SCRIPT_DIR/mcp-bash-wrapper.js" "$config_file" 2>/dev/null; then
            print_pass "Config points to current installation"
        else
            print_warn "Config may point to different installation"
            print_info "Expected: $SCRIPT_DIR/mcp-bash-wrapper.js"
        fi
    else
        print_warn "bash server not found in config"
        print_info "Add to config:"
        echo ""
        echo "{
  \"mcpServers\": {
    \"bash\": {
      \"command\": \"node\",
      \"args\": [\"$SCRIPT_DIR/mcp-bash-wrapper.js\"]
    }
  }
}"
        echo ""
    fi
}

# Test 7: Check permissions
test_permissions() {
    print_test "File permissions"

    if [ -x "$SCRIPT_DIR/mcp-bash-wrapper.js" ]; then
        print_pass "mcp-bash-wrapper.js is executable"
    else
        print_warn "mcp-bash-wrapper.js not executable (not required, but recommended)"
        print_info "Fix: chmod +x mcp-bash-wrapper.js"
    fi

    if [ -x "$SCRIPT_DIR/install.sh" ]; then
        print_pass "install.sh is executable"
    else
        print_warn "install.sh not executable"
    fi

    if [ -x "$SCRIPT_DIR/verify.sh" ]; then
        print_pass "verify.sh is executable"
    else
        print_warn "verify.sh not executable"
    fi
}

# Generate summary report
print_summary() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Verification Summary                 ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All critical tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Configure Claude Desktop (if not done)"
        echo "  2. Restart Claude Desktop"
        echo "  3. Test in Claude Desktop with a simple bash command"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Review failed tests above"
        echo "  2. Run: npm install && pip3 install -e ."
        echo "  3. Check README.md for detailed instructions"
        echo ""
        return 1
    fi
}

# Main verification flow
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║     Advanced MCP Bash Server - Verification Script      ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    test_binaries
    test_project_files
    test_node_deps
    test_python_deps
    test_server_startup
    test_mcp_config
    test_permissions

    print_summary
}

main
exit $?

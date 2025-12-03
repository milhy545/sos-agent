#!/bin/bash

# 🆘 SOS Agent - Standalone Installer
# Automatic installation script for any Linux system

set -e

INSTALL_DIR="$HOME/.sos-agent"
BIN_DIR="$HOME/.local/bin"
VENV_DIR="$INSTALL_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════╗
║                                           ║
║     🆘  SOS AGENT INSTALLER  🆘           ║
║                                           ║
║   AI-Powered System Rescue Agent          ║
║                                           ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check Python 3.11+
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found! Please install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo -e "${RED}❌ Python $PYTHON_VERSION found, but Python 3.11+ required!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"

# Create installation directory
echo -e "${YELLOW}[2/6] Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
cd "$INSTALL_DIR"

# Download or copy source code
echo -e "${YELLOW}[3/6] Installing SOS Agent...${NC}"

# Check if running from source directory
if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    echo "Installing from local source..."
    cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR"/.[!.]* "$INSTALL_DIR/" 2>/dev/null || true
else
    echo -e "${RED}Error: pyproject.toml not found in $SCRIPT_DIR${NC}"
    echo -e "${RED}Please run this script from the SOS Agent directory${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}[4/6] Setting up Python environment...${NC}"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install pip and dependencies
echo -e "${YELLOW}[5/6] Installing dependencies (this may take a minute)...${NC}"
pip install --quiet --upgrade pip setuptools wheel

# Install poetry and project
pip install --quiet poetry
poetry install --quiet --no-interaction

# Create global launcher script
echo -e "${YELLOW}[6/6] Creating global 'sos' command...${NC}"

cat > "$BIN_DIR/sos" << 'EOFBIN'
#!/bin/bash
INSTALL_DIR="$HOME/.sos-agent"
VENV_DIR="$INSTALL_DIR/venv"

# Load environment variables from .env
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
fi

# Activate venv and run
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR"
poetry run sos "$@"
EOFBIN

chmod +x "$BIN_DIR/sos"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Adding $HOME/.local/bin to PATH...${NC}"

    # Detect shell and add to appropriate rc file
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi

    echo "" >> "$SHELL_RC"
    echo '# SOS Agent PATH' >> "$SHELL_RC"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"

    export PATH="$HOME/.local/bin:$PATH"

    echo -e "${GREEN}✅ PATH updated in $SHELL_RC${NC}"
fi

# Setup wizard
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🎉  Installation Complete!  🎉          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Ask if user wants to configure API keys now
echo -e "${YELLOW}Do you want to configure API keys now? (y/n)${NC}"
read -r CONFIGURE_NOW

if [[ "$CONFIGURE_NOW" =~ ^[Yy]$ ]]; then
    "$BIN_DIR/sos" setup
fi

echo ""
echo -e "${GREEN}✅ SOS Agent is ready!${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo -e "  ${GREEN}sos setup${NC}              # Configure API keys"
echo -e "  ${GREEN}sos diagnose --category hardware${NC}  # Run hardware diagnostics"
echo -e "  ${GREEN}sos diagnose --category network${NC}   # Check network issues"
echo -e "  ${GREEN}sos diagnose --category all${NC}       # Full system scan"
echo -e "  ${GREEN}sos --help${NC}             # Show all commands"
echo ""

# If PATH was updated, remind to reload shell
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️  Please restart your terminal or run:${NC}"
    echo -e "  ${GREEN}source $SHELL_RC${NC}"
    echo ""
fi

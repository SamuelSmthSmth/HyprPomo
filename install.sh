#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

REPO_URL="https://raw.githubusercontent.com/SamuelSmthSmth/HyprPomo/main/hypr_pomo.py"
INSTALL_DIR="$HOME/.local/bin"
SCRIPT_NAME="hypr_pomo.py"
ALIAS_NAME="timer"

echo -e "${BLUE}🍅 Installing HyprPomo...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing Python dependencies (rich)...${NC}"
pip3 install rich --user --break-system-packages 2>/dev/null || pip3 install rich --user

echo -e "${BLUE}📂 Setting up directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.config/hypr_pomo"
mkdir -p "$HOME/.local/share/hypr_pomo"

echo -e "${BLUE}⬇️  Downloading HyprPomo...${NC}"
curl -sL "$REPO_URL" -o "$INSTALL_DIR/$SCRIPT_NAME"

if [ ! -f "$INSTALL_DIR/$SCRIPT_NAME" ]; then
    echo -e "${RED}Error: Failed to download script.${NC}"
    exit 1
fi

chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
echo -e "${GREEN}✅ Script installed to $INSTALL_DIR/$SCRIPT_NAME${NC}"

SHELL_NAME=$(basename "$SHELL")
CONFIG_FILE=""

case "$SHELL_NAME" in
    "fish")
        CONFIG_FILE="$HOME/.config/fish/config.fish"
        if ! grep -q "function $ALIAS_NAME" "$CONFIG_FILE"; then
            echo -e "\n# HyprPomo Timer" >> "$CONFIG_FILE"
            echo "function $ALIAS_NAME" >> "$CONFIG_FILE"
            echo "    python3 $INSTALL_DIR/$SCRIPT_NAME \$argv" >> "$CONFIG_FILE"
            echo "end" >> "$CONFIG_FILE"
            echo -e "${GREEN}🐟 Added 'timer' function to Fish config.${NC}"
        else
            echo -e "${BLUE}ℹ️  'timer' function already exists in Fish config.${NC}"
        fi
        ;;
    "bash")
        CONFIG_FILE="$HOME/.bashrc"
        if ! grep -q "alias $ALIAS_NAME=" "$CONFIG_FILE"; then
            echo -e "\n# HyprPomo Timer" >> "$CONFIG_FILE"
            echo "alias $ALIAS_NAME='python3 $INSTALL_DIR/$SCRIPT_NAME'" >> "$CONFIG_FILE"
            echo -e "${GREEN}🐚 Added 'timer' alias to .bashrc.${NC}"
        fi
        ;;
    "zsh")
        CONFIG_FILE="$HOME/.zshrc"
        if ! grep -q "alias $ALIAS_NAME=" "$CONFIG_FILE"; then
            echo -e "\n# HyprPomo Timer" >> "$CONFIG_FILE"
            echo "alias $ALIAS_NAME='python3 $INSTALL_DIR/$SCRIPT_NAME'" >> "$CONFIG_FILE"
            echo -e "${GREEN}💤 Added 'timer' alias to .zshrc.${NC}"
        fi
        ;;
    *)
        echo -e "${RED}⚠️  Unknown shell: $SHELL_NAME. Please add the alias manually:${NC}"
        echo "alias $ALIAS_NAME='python3 $INSTALL_DIR/$SCRIPT_NAME'"
        ;;
esac

echo -e "\n${GREEN}🎉 Installation Complete!${NC}"
echo -e "Please restart your terminal or source your config file."
echo -e "Try running: ${BLUE}timer help${NC}"

#!/bin/bash
# Installation script for git-auto-commit

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="/usr/local/bin"
SCRIPT_PATH="$SCRIPT_DIR/git-auto-commit.py"

# Make the script executable
chmod +x "$SCRIPT_PATH"

# Create symbolic link
echo "Creating symbolic link to git-auto-commit.py in $TARGET_DIR..."
if [ -w "$TARGET_DIR" ]; then
    ln -sf "$SCRIPT_PATH" "$TARGET_DIR/git-autocommit"
    echo "Symbolic link created successfully!"
else
    echo "Error: You don't have write permission to $TARGET_DIR"
    echo "Please run this script with sudo or manually create a symbolic link:"
    echo "sudo ln -sf \"$SCRIPT_PATH\" \"$TARGET_DIR/git-autocommit\""
    exit 1
fi

# Install dependencies
echo "Installing required Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt"

echo "Installation complete! You can now use 'git autocommit' command."
echo "To set up a configuration file in your git repository, run:"
echo "git autocommit --setup"

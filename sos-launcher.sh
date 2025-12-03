#!/bin/zsh
# SOS Agent Launcher - ensures correct PATH and environment

# Add Poetry to PATH
export PATH="/home/milhy777/.local/bin:$PATH"

# Change to project directory
cd /home/milhy777/Develop/Production/sos-agent

# Run SOS agent with all arguments
exec /home/milhy777/.local/bin/poetry run sos "$@"

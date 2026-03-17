#!/bin/bash
# ====================================
# PM Agent Startup Script
# ====================================

echo ""
echo "========================================"
echo "  PM Agent - Project Manager"
echo "========================================"
echo ""
echo "Starting PM Agent..."
echo ""

# Check if in correct directory
if [ ! -f "agents/pm/AGENTS.md" ]; then
    echo "Error: Not in PM Agent template directory!"
    echo "Please run this script from the template root."
    exit 1
fi

# Start OpenCode with PM Agent
opencode --agent pm

#!/bin/bash

# Supabase MCP Installer - Automated Setup Script
# Version: 1.0.0
# Description: One-shot installation of Supabase MCP with proper authentication

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════╗"
echo "║   Supabase MCP Installer v1.0.0               ║"
echo "║   One-Shot Installation & Configuration       ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo ""
echo "═══ Step 1: Checking Prerequisites ═══"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js found: $NODE_VERSION"

# Check Claude CLI
if ! command -v claude &> /dev/null; then
    print_error "Claude CLI is not installed. Please install Claude Code first."
    exit 1
fi
print_success "Claude CLI found"

# Check if we're in a project directory
if [ ! -f "package.json" ] && [ ! -f ".env" ]; then
    print_warning "Not in a typical project directory. Continuing anyway..."
fi

echo ""
echo "═══ Step 2: Supabase Project Setup ═══"
echo ""

print_info "Do you have a Supabase project already? (y/n)"
read -r has_project

if [ "$has_project" != "y" ]; then
    echo ""
    print_info "Please create a Supabase project first:"
    echo ""
    echo "1. Go to: https://supabase.com"
    echo "2. Click 'Start your project' and sign in"
    echo "3. Click 'New Project'"
    echo "4. Fill in:"
    echo "   - Project Name: your-project-name"
    echo "   - Database Password: (choose a strong password)"
    echo "   - Region: (select closest to you)"
    echo "5. Wait 2-3 minutes for project creation"
    echo ""
    print_info "Press ENTER when your project is ready..."
    read -r
fi

echo ""
echo "═══ Step 3: Collecting Credentials ═══"
echo ""

print_info "Let's collect your Supabase credentials."
echo ""

# Get Project URL
print_info "Enter your Supabase Project URL"
echo "  (Found in: Project Settings → API → Project URL)"
echo "  (Example: https://xxxxx.supabase.co)"
read -r SUPABASE_URL

if [ -z "$SUPABASE_URL" ]; then
    print_error "Project URL is required!"
    exit 1
fi
print_success "Project URL saved"

# Get Anon Key
echo ""
print_info "Enter your Supabase Anon/Public Key"
echo "  (Found in: Project Settings → API → anon public)"
echo "  (Starts with: eyJ...)"
read -r SUPABASE_ANON_KEY

if [ -z "$SUPABASE_ANON_KEY" ]; then
    print_error "Anon key is required!"
    exit 1
fi
print_success "Anon key saved"

# Get Service Role Key
echo ""
print_info "Enter your Supabase Service Role Key"
echo "  (Found in: Project Settings → API → service_role - click 'Reveal')"
echo "  (Starts with: eyJ...)"
read -r SUPABASE_SERVICE_ROLE_KEY

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    print_error "Service role key is required!"
    exit 1
fi
print_success "Service role key saved"

# Get Personal Access Token (CRITICAL!)
echo ""
print_warning "⚠️  CRITICAL: Personal Access Token Required!"
echo ""
print_info "The MCP server requires a Personal Access Token (PAT), not just project keys."
echo ""
echo "To get your PAT:"
echo "1. Click your profile icon (top right)"
echo "2. Select 'Account Settings'"
echo "3. Click 'Access Tokens' in left menu"
echo "4. Click 'Generate New Token'"
echo "5. Name it: 'Claude Code MCP'"
echo "6. Copy the token (starts with sbp_)"
echo ""
print_info "Enter your Personal Access Token:"
read -r SUPABASE_ACCESS_TOKEN

if [ -z "$SUPABASE_ACCESS_TOKEN" ]; then
    print_error "Personal Access Token is required for MCP authentication!"
    exit 1
fi

if [[ ! "$SUPABASE_ACCESS_TOKEN" =~ ^sbp_ ]]; then
    print_warning "Warning: Token doesn't start with 'sbp_'. Are you sure this is correct?"
    print_info "Continue anyway? (y/n)"
    read -r continue_anyway
    if [ "$continue_anyway" != "y" ]; then
        print_error "Installation cancelled. Please get the correct PAT."
        exit 1
    fi
fi
print_success "Personal Access Token saved"

echo ""
echo "═══ Step 4: Creating .env File ═══"
echo ""

# Check if .env exists
if [ -f .env ]; then
    print_warning ".env file already exists!"
    print_info "Do you want to:"
    echo "  1) Append Supabase config (keep existing)"
    echo "  2) Overwrite entire file"
    echo "  3) Skip .env creation"
    read -r env_choice

    case $env_choice in
        1)
            echo "" >> .env
            echo "# Supabase Configuration (added by supabase-mcp-installer)" >> .env
            ;;
        2)
            cp .env .env.backup
            print_info "Backed up existing .env to .env.backup"
            cat /dev/null > .env
            ;;
        3)
            print_info "Skipping .env creation"
            ;;
        *)
            print_error "Invalid choice. Skipping .env creation."
            ;;
    esac
fi

# Write Supabase config to .env
if [ "$env_choice" != "3" ]; then
    cat >> .env << EOF

# Supabase Project Configuration
SUPABASE_URL=$SUPABASE_URL
SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY

# Supabase Personal Access Token (REQUIRED for MCP!)
SUPABASE_ACCESS_TOKEN=$SUPABASE_ACCESS_TOKEN

# Vite/Application Configuration
VITE_SUPABASE_URL=$SUPABASE_URL
VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
VITE_SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
EOF
    print_success ".env file updated with Supabase credentials"
fi

echo ""
echo "═══ Step 5: Installing Supabase MCP Server ═══"
echo ""

# Remove existing supabase MCP if present
print_info "Removing any existing Supabase MCP configuration..."
claude mcp remove supabase 2>/dev/null || true

# Install MCP server with correct package and credentials
print_info "Installing Supabase MCP server with authentication..."
echo ""

claude mcp add supabase npx @supabase/mcp-server-supabase \
  --env SUPABASE_URL="$SUPABASE_URL" \
  --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN"

echo ""
print_success "Supabase MCP server installed!"

echo ""
echo "═══ Step 6: Verifying Connection ═══"
echo ""

print_info "Checking MCP server status..."
sleep 2  # Give it a moment to initialize

# Check connection status
if claude mcp list | grep -q "supabase.*Connected"; then
    print_success "Connection successful! Supabase MCP is ready to use! 🎉"
    echo ""
    echo "═══════════════════════════════════════════════"
    echo ""
    print_success "Installation Complete!"
    echo ""
    echo "Your Supabase MCP server is now connected and ready."
    echo ""
    echo "Next steps:"
    echo "  • Test the connection: ./scripts/verify-connection.sh"
    echo "  • Use Supabase MCP tools in Claude Code"
    echo "  • Start building with Supabase!"
    echo ""
    echo "═══════════════════════════════════════════════"
elif claude mcp list | grep -q "supabase.*authentication"; then
    print_error "Connection failed - needs authentication"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify your Personal Access Token is correct"
    echo "2. Check it starts with 'sbp_'"
    echo "3. Ensure it hasn't been revoked"
    echo "4. Try running: ./scripts/diagnose.sh"
    echo ""
    print_info "Run setup again with correct credentials? (y/n)"
    read -r retry
    if [ "$retry" == "y" ]; then
        exec "$0"  # Re-run this script
    fi
elif claude mcp list | grep -q "supabase.*Failed"; then
    print_error "Connection failed"
    echo ""
    echo "Common issues:"
    echo "1. Wrong Personal Access Token"
    echo "2. Incorrect project URL"
    echo "3. Network connectivity issues"
    echo ""
    print_info "Run diagnostics: ./scripts/diagnose.sh"
else
    print_warning "Could not determine connection status"
    echo ""
    print_info "Run verification manually: claude mcp list"
fi

echo ""
print_info "Installation log saved to: supabase-mcp-install.log"

# Save installation details to log
cat > supabase-mcp-install.log << EOF
Supabase MCP Installation Log
=============================
Date: $(date)
Project URL: $SUPABASE_URL
MCP Package: @supabase/mcp-server-supabase
Status: $(claude mcp list | grep supabase || echo "Unknown")

Configuration:
- SUPABASE_URL: Set
- SUPABASE_ANON_KEY: Set
- SUPABASE_ACCESS_TOKEN: Set

.env file: Updated
MCP Server: Installed

To verify connection: ./scripts/verify-connection.sh
To troubleshoot: ./scripts/diagnose.sh
EOF

print_success "Setup complete!"

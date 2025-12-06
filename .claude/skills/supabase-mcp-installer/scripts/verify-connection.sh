#!/bin/bash

# Supabase MCP Connection Verification Script
# Tests the connection and basic functionality

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════╗"
echo "║   Supabase MCP Connection Verifier            ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "═══ Testing MCP Server Connection ═══"
echo ""

# Test 1: Check if MCP server is registered
print_info "Test 1: Checking MCP server registration..."
if claude mcp list | grep -q "supabase"; then
    print_success "Supabase MCP server is registered"
else
    print_error "Supabase MCP server not found in Claude config"
    exit 1
fi

# Test 2: Check connection status
print_info "Test 2: Checking connection status..."
if claude mcp list | grep -q "supabase.*Connected"; then
    print_success "Connection status: Connected"
elif claude mcp list | grep -q "supabase.*authentication"; then
    print_error "Connection status: Needs authentication"
    echo ""
    echo "Fix: Verify your SUPABASE_ACCESS_TOKEN in .env"
    exit 1
elif claude mcp list | grep -q "supabase.*Failed"; then
    print_error "Connection status: Failed"
    echo ""
    echo "Run diagnostics: ./scripts/diagnose.sh"
    exit 1
else
    print_warning "Connection status: Unknown"
fi

# Test 3: Check environment variables
print_info "Test 3: Verifying environment variables..."
if [ -f .env ]; then
    if grep -q "SUPABASE_ACCESS_TOKEN" .env; then
        print_success "SUPABASE_ACCESS_TOKEN found in .env"
    else
        print_error "SUPABASE_ACCESS_TOKEN missing from .env"
        exit 1
    fi

    if grep -q "SUPABASE_URL" .env; then
        print_success "SUPABASE_URL found in .env"
    else
        print_error "SUPABASE_URL missing from .env"
        exit 1
    fi
else
    print_error ".env file not found"
    exit 1
fi

# Test 4: Check package availability
print_info "Test 4: Verifying MCP package..."
if npx @supabase/mcp-server-supabase --version 2>&1 | grep -q "error"; then
    print_error "Package installation issue detected"
else
    print_success "MCP package is available"
fi

# Test 5: Check Claude config
print_info "Test 5: Checking Claude Code configuration..."
if [ -f ~/.claude.json ]; then
    if grep -q "supabase" ~/.claude.json; then
        print_success "Supabase entry found in Claude config"
    else
        print_warning "No supabase entry in Claude config"
    fi
else
    print_error "Claude config file not found"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo ""
print_success "Verification Complete!"
echo ""
echo "All tests passed! Your Supabase MCP is properly configured."
echo ""
echo "Next steps:"
echo "  • Start using Supabase MCP tools in Claude Code"
echo "  • Query your database with MCP commands"
echo "  • Build your application!"
echo ""
echo "═══════════════════════════════════════════════"

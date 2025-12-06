#!/bin/bash

# Supabase MCP Diagnostic Tool
# Comprehensive diagnostics for troubleshooting

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
echo "║   Supabase MCP Diagnostic Tool                ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "═══ 1️⃣ Checking .env File ═══"
echo ""

if [ -f .env ]; then
    print_success ".env file exists"

    if grep -q "SUPABASE_ACCESS_TOKEN" .env; then
        print_success "SUPABASE_ACCESS_TOKEN found"
        TOKEN=$(grep "^SUPABASE_ACCESS_TOKEN" .env | cut -d '=' -f2)
        if [[ "$TOKEN" =~ ^sbp_ ]]; then
            print_success "Token format is correct (starts with sbp_)"
        else
            print_error "Token doesn't start with 'sbp_' - might be incorrect!"
        fi
    else
        print_error "SUPABASE_ACCESS_TOKEN missing!"
        echo "  This is the #1 cause of connection failures."
        echo "  Get it from: https://supabase.com/dashboard/account/tokens"
    fi

    if grep -q "SUPABASE_URL" .env; then
        print_success "SUPABASE_URL found"
        URL=$(grep "^SUPABASE_URL" .env | cut -d '=' -f2)
        echo "  URL: $URL"
    else
        print_error "SUPABASE_URL missing!"
    fi

    if grep -q "SUPABASE_ANON_KEY" .env; then
        print_success "SUPABASE_ANON_KEY found"
    else
        print_error "SUPABASE_ANON_KEY missing!"
    fi
else
    print_error ".env file not found!"
    echo "  Run ./scripts/setup.sh to create it."
fi

echo ""
echo "═══ 2️⃣ Checking MCP Installation ═══"
echo ""

print_info "MCP server status:"
claude mcp list | grep supabase || print_error "Supabase MCP not found"

echo ""
echo "═══ 3️⃣ Testing Package Availability ═══"
echo ""

print_info "Testing @supabase/mcp-server-supabase package..."
if command -v npx &> /dev/null; then
    print_success "npx is available"
    npx @supabase/mcp-server-supabase --version 2>&1 | head -5
else
    print_error "npx not found"
fi

echo ""
echo "═══ 4️⃣ Checking Claude Code Config ═══"
echo ""

if [ -f ~/.claude.json ]; then
    print_success "Claude config exists"
    if grep -q "supabase" ~/.claude.json; then
        print_success "Supabase entry found in config"
        echo ""
        print_info "Config snippet:"
        grep -A 10 "supabase" ~/.claude.json | head -12
    else
        print_warning "No supabase entry in config"
        echo "  The MCP server might not be installed."
    fi
else
    print_error "Claude config not found at ~/.claude.json"
fi

echo ""
echo "═══ 5️⃣ Environment Variable Test ═══"
echo ""

if [ -f .env ]; then
    source .env
    if [ -n "$SUPABASE_URL" ]; then
        print_success "SUPABASE_URL loads correctly: ${SUPABASE_URL:0:30}..."
    else
        print_error "SUPABASE_URL not loading from .env"
    fi

    if [ -n "$SUPABASE_ACCESS_TOKEN" ]; then
        print_success "SUPABASE_ACCESS_TOKEN loads correctly (${#SUPABASE_ACCESS_TOKEN} chars)"
    else
        print_error "SUPABASE_ACCESS_TOKEN not loading from .env"
    fi
fi

echo ""
echo "═══ 6️⃣ Node.js & NPM Info ═══"
echo ""

if command -v node &> /dev/null; then
    print_success "Node.js version: $(node --version)"
else
    print_error "Node.js not found"
fi

if command -v npm &> /dev/null; then
    print_success "npm version: $(npm --version)"
else
    print_error "npm not found"
fi

echo ""
echo "═══ 7️⃣ Network Test ═══"
echo ""

if [ -f .env ] && grep -q "SUPABASE_URL" .env; then
    source .env
    print_info "Testing connection to Supabase..."
    if curl -s --head "$SUPABASE_URL" | grep "200\|301\|302" > /dev/null; then
        print_success "Supabase project is reachable"
    else
        print_warning "Could not reach Supabase project"
        echo "  This might be a network issue or the URL is incorrect."
    fi
fi

echo ""
echo "═══════════════════════════════════════════════"
echo ""
print_info "Diagnostic Summary"
echo ""

# Count issues
ISSUES=0

if [ ! -f .env ]; then ((ISSUES++)); fi
if ! grep -q "SUPABASE_ACCESS_TOKEN" .env 2>/dev/null; then ((ISSUES++)); fi
if ! claude mcp list | grep -q "supabase.*Connected" 2>/dev/null; then ((ISSUES++)); fi

if [ $ISSUES -eq 0 ]; then
    print_success "No issues detected! Everything looks good."
else
    print_warning "Found $ISSUES potential issue(s)"
    echo ""
    echo "Common fixes:"
    echo "  1. Re-run setup: ./scripts/setup.sh"
    echo "  2. Verify Personal Access Token at:"
    echo "     https://supabase.com/dashboard/account/tokens"
    echo "  3. Check project status at:"
    echo "     https://supabase.com/dashboard"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo ""
print_info "Diagnostic complete!"
echo ""
echo "For help, see:"
echo "  • SKILL.md troubleshooting section"
echo "  • docs/TROUBLESHOOTING.md"
echo "  • https://supabase.com/docs"

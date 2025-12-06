# Supabase MCP Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: `✗ Failed to connect`

**Symptoms:**
```bash
$ claude mcp list
supabase: npx @supabase/mcp-server-supabase - ✗ Failed to connect
```

**Most Common Cause:** Missing or incorrect Personal Access Token

**Solutions:**

1. **Verify PAT exists in .env:**
   ```bash
   grep SUPABASE_ACCESS_TOKEN .env
   ```

   Should show:
   ```
   SUPABASE_ACCESS_TOKEN=sbp_...
   ```

2. **Check PAT format:**
   - Must start with `sbp_`
   - Should be 40+ characters
   - No quotes around the value in .env

3. **Get a new PAT:**
   - Go to: https://supabase.com/dashboard/account/tokens
   - Click "Generate New Token"
   - Name it: "Claude Code MCP"
   - Copy immediately (you can't see it again!)
   - Update .env file
   - Reinstall MCP:
     ```bash
     claude mcp remove supabase
     source .env
     claude mcp add supabase npx @supabase/mcp-server-supabase \
       --env SUPABASE_URL="$SUPABASE_URL" \
       --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
       --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN"
     ```

---

### Issue 2: `⚠ Needs authentication`

**Symptoms:**
```bash
supabase: npx @supabase/mcp-server-supabase - ⚠ Needs authentication
```

**Cause:** Environment variables not passed to MCP server

**Solutions:**

1. **Verify .env file location:**
   ```bash
   ls -la .env
   ```
   Must be in project root!

2. **Check .env format (no spaces!):**
   ```bash
   # ✅ CORRECT
   SUPABASE_ACCESS_TOKEN=sbp_abc123

   # ❌ WRONG (space before/after =)
   SUPABASE_ACCESS_TOKEN = sbp_abc123
   ```

3. **Reinstall with explicit sourcing:**
   ```bash
   claude mcp remove supabase
   source .env  # Load env vars into current shell
   claude mcp add supabase npx @supabase/mcp-server-supabase \
     --env SUPABASE_URL="${SUPABASE_URL}" \
     --env SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}" \
     --env SUPABASE_ACCESS_TOKEN="${SUPABASE_ACCESS_TOKEN}"
   ```

4. **Use hardcoded values (temporary debugging):**
   ```bash
   claude mcp add supabase npx @supabase/mcp-server-supabase \
     --env SUPABASE_URL="https://yourproject.supabase.co" \
     --env SUPABASE_ANON_KEY="eyJhbG..." \
     --env SUPABASE_ACCESS_TOKEN="sbp_..."
   ```

---

### Issue 3: `TypeError [ERR_PARSE_ARGS_UNKNOWN_OPTION]`

**Symptoms:**
```
TypeError [ERR_PARSE_ARGS_UNKNOWN_OPTION]: Unknown option '--help'
    at checkOptionUsage (node:internal/util/parse_args/parse_args:107:13)
```

**Cause:** Wrong package name used

**Solutions:**

❌ **WRONG packages:**
```bash
@modelcontextprotocol/server-supabase  # Doesn't exist
@anthropic-ai/mcp-server-supabase      # Wrong namespace
@supabase/mcp                          # Incomplete name
```

✅ **CORRECT package:**
```bash
@supabase/mcp-server-supabase
```

**Fix:**
```bash
claude mcp remove supabase
claude mcp add supabase npx @supabase/mcp-server-supabase ...
```

---

### Issue 4: `npm warn exec The following package was not found`

**Symptoms:**
```
npm warn exec The following package was not found and will be installed: @supabase/mcp-server-supabase@0.5.9
```

**This is NORMAL!**

NPX downloads packages on first use. Just wait for it to complete.

**If it actually fails:**
```bash
# Clear NPX cache
npx clear-npx-cache

# Or manually
rm -rf ~/.npm/_npx

# Try again
claude mcp add supabase npx @supabase/mcp-server-supabase ...
```

---

### Issue 5: Environment variables not loading

**Symptoms:**
- MCP installs but can't connect
- Variables show as empty

**Solutions:**

1. **Check .env location:**
   ```bash
   pwd           # Verify you're in project root
   ls -la .env   # Verify .env exists here
   ```

2. **Test .env loading:**
   ```bash
   source .env
   echo $SUPABASE_URL
   # Should print your URL
   ```

3. **Check for syntax errors:**
   ```bash
   # Common mistakes:
   SUPABASE_URL = https://...     # ❌ Spaces around =
   SUPABASE_URL= https://...      # ❌ Space after =
   SUPABASE_URL =https://...      # ❌ Space before =
   SUPABASE_URL=https://...       # ✅ No spaces!
   ```

4. **Check for hidden characters:**
   ```bash
   cat -A .env
   # Look for weird symbols (^M, etc.)
   ```

---

### Issue 6: Connection works then stops

**Symptoms:**
- Was working, now shows "Failed to connect"
- No changes made to configuration

**Causes & Solutions:**

1. **Token revoked:**
   - Go to: https://supabase.com/dashboard/account/tokens
   - Check if token shows "Revoked"
   - If yes, generate new token and update .env

2. **Project paused (free tier):**
   - Go to project dashboard
   - Look for "Project Paused" banner
   - Click "Resume Project"
   - Wait 2-3 minutes for startup

3. **Supabase maintenance:**
   - Check: https://status.supabase.com
   - Wait for maintenance to complete

---

### Issue 7: MCP server crashes on startup

**Symptoms:**
```bash
$ claude mcp list
supabase: npx @supabase/mcp-server-supabase - ✗ Failed to connect (crashed)
```

**Solutions:**

1. **Check Node.js version:**
   ```bash
   node --version
   # Should be v18.0.0 or higher
   ```

2. **Update MCP package:**
   ```bash
   npx clear-npx-cache
   claude mcp remove supabase
   # Reinstall to get latest version
   ```

3. **Check Claude Code logs:**
   ```bash
   tail -f ~/.claude/logs/mcp-servers.log
   ```

4. **Test package directly:**
   ```bash
   source .env
   npx @supabase/mcp-server-supabase
   # Look for error messages
   ```

---

### Issue 8: Can't access database/tables

**Symptoms:**
- MCP connected
- But queries fail or return empty

**Solutions:**

1. **Check service role key:**
   - Must use `service_role` key, not `anon` key
   - Verify in .env:
     ```bash
     grep SERVICE_ROLE .env
     ```

2. **Verify table exists:**
   - Go to Supabase dashboard
   - Check Table Editor
   - Confirm table name spelling

3. **Check RLS policies:**
   - Row Level Security might block access
   - Temporarily disable to test:
     - Table Editor → RLS → Disable
   - Re-enable after testing!

4. **Test with Supabase CLI:**
   ```bash
   npx supabase db diff
   ```

---

### Issue 9: Wrong project connected

**Symptoms:**
- Different database than expected
- Tables don't match

**Solution:**

1. **Verify project URL:**
   ```bash
   grep SUPABASE_URL .env
   ```

2. **Check in Supabase dashboard:**
   - Click project name (top left)
   - Verify it's the correct project
   - Get correct URL from Settings → API

3. **Update and reinstall:**
   ```bash
   # Update .env with correct URL
   nano .env

   # Reinstall MCP
   claude mcp remove supabase
   ./scripts/setup.sh  # Or manual install
   ```

---

### Issue 10: `ECONNREFUSED` or network errors

**Symptoms:**
```
Error: connect ECONNREFUSED
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping supabase.com
   ```

2. **Test Supabase directly:**
   ```bash
   curl -I https://your-project.supabase.co
   ```

3. **Check firewall/VPN:**
   - Disable VPN temporarily
   - Check corporate firewall settings

4. **Verify project is running:**
   - Go to project dashboard
   - Should show "Healthy" status

---

## Diagnostic Commands

### Quick health check:
```bash
./scripts/diagnose.sh
```

### Manual checks:
```bash
# 1. Check MCP status
claude mcp list

# 2. Verify .env
cat .env | grep SUPABASE

# 3. Test package
npx @supabase/mcp-server-supabase --version

# 4. Check Claude config
cat ~/.claude.json | grep -A 10 supabase

# 5. Test connection
curl -I "$(grep SUPABASE_URL .env | cut -d= -f2)"
```

---

## Getting Help

If none of these solutions work:

1. **Run full diagnostics:**
   ```bash
   ./scripts/diagnose.sh > diagnostic-report.txt
   ```

2. **Check official docs:**
   - Supabase: https://supabase.com/docs
   - Claude MCP: https://docs.claude.com/en/docs/claude-code/mcp

3. **File an issue:**
   - Include diagnostic report
   - Describe what you've tried
   - Include error messages

---

## Prevention Tips

1. **Secure your tokens:**
   - Never commit .env to git
   - Add `.env` to .gitignore
   - Rotate tokens periodically

2. **Document your setup:**
   - Keep notes on which project
   - Save credentials securely (password manager)

3. **Regular testing:**
   ```bash
   ./scripts/verify-connection.sh
   ```

4. **Monitor Supabase status:**
   - Bookmark: https://status.supabase.com
   - Subscribe to updates

---

**Last Updated:** October 31, 2025
**Covers:** Supabase MCP v0.5.9+, Claude Code 2.0+

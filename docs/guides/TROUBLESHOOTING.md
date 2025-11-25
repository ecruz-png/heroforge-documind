# Troubleshooting Guide

## Environment Setup Issues

### Codespace Won't Start
**Symptoms:** Codespace initialization hangs or fails

**Solutions:**
1. Refresh the page and wait 2-3 minutes
2. Click "..." → "Delete codespace" and create a new one
3. Try a different browser (Chrome recommended)
4. Check GitHub Status: https://www.githubstatus.com/

### "dsp: command not found"
**Symptoms:** Claude Code CLI not recognized

**Solutions:**
```bash
# Reload shell configuration
source ~/.bashrc

# If still not working, reinstall:
npm install -g @anthropic-ai/claude-code
```

### API Key Errors
**Symptoms:** "Invalid API key" or "Authentication failed"

**Solutions:**
1. Check `.env` file format:
   - No quotes around values
   - No spaces around `=`
   - Key starts with correct prefix (`sk-ant-`, `sk-`, etc.)

2. Verify key is active:
   - Log into Anthropic Console and check key status
   - Try creating a new key

3. Reload environment:
   ```bash
   source .env
   echo $ANTHROPIC_API_KEY
   ```

### npm install Fails
**Symptoms:** Errors during dependency installation

**Solutions:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Tests Failing
**Symptoms:** `npm test` shows failures

**Solutions:**
1. Check `.env` file exists and has correct format
2. Ensure all dependencies installed: `npm install`
3. Check specific error messages for clues

## Session-Specific Issues

### Session 3: Skills Not Loading
**Symptoms:** `/skill [name]` returns "not found"

**Solutions:**
1. Verify file path: `.claude/skills/[name].md`
2. Check file has content (not empty)
3. Restart `dsp` session

### Session 4: Database Connection Failed
**Symptoms:** Cannot connect to Supabase

**Solutions:**
1. Verify Supabase project is not paused (free tier pauses after inactivity)
2. Check URL and keys in `.env`
3. Test connection in Supabase Dashboard SQL Editor

### Session 5: Agents Not Spawning
**Symptoms:** Swarm init fails or agents don't respond

**Solutions:**
1. Check Claude Flow is installed: `npx claude-flow@alpha --version`
2. Restart Codespace
3. Reduce max agents (try 2 instead of 4)

## Still Stuck?

1. Check error messages carefully - they often tell you exactly what's wrong
2. Search existing GitHub Issues
3. Ask in course chat/Discord with:
   - What you were trying to do
   - Exact error message
   - What you've already tried

# Advanced Supabase MCP Configuration

## Multiple Projects

### Managing Multiple Supabase Projects

If you work with multiple Supabase projects, you can switch between them:

#### Option 1: Multiple .env Files

```bash
# Create project-specific .env files
.env.production
.env.staging
.env.development

# Switch between them
cp .env.production .env
claude mcp remove supabase
source .env
claude mcp add supabase npx @supabase/mcp-server-supabase \
  --env SUPABASE_URL="$SUPABASE_URL" \
  --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN"
```

#### Option 2: Project Switcher Script

```bash
#!/bin/bash
# switch-supabase.sh

PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo "Usage: ./switch-supabase.sh [production|staging|development]"
    exit 1
fi

cp .env.$PROJECT .env
source .env

claude mcp remove supabase
claude mcp add supabase npx @supabase/mcp-server-supabase \
  --env SUPABASE_URL="$SUPABASE_URL" \
  --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN"

echo "Switched to $PROJECT project"
claude mcp list | grep supabase
```

Usage:
```bash
chmod +x switch-supabase.sh
./switch-supabase.sh production
```

---

## Integration with Claude Flow GOAP

### Using Goal-Oriented Action Planning for Supabase Architecture

The Supabase MCP skill integrates with claude-flow's GOAP system for intelligent database design:

```bash
# Initialize GOAP planning for complete backend setup
npx claude-flow@alpha goap plan "Design and implement complete Supabase backend with authentication, storage, and real-time features"
```

### Example GOAP Workflow

```typescript
// Define current state
const currentState = {
  supabase_mcp_connected: true,
  project_created: true,
  credentials_configured: true
};

// Define goal state
const goalState = {
  auth_configured: true,
  user_table_created: true,
  rls_policies_active: true,
  storage_buckets_configured: true,
  realtime_enabled: true,
  api_endpoints_documented: true
};

// GOAP will create an optimal action plan
```

### Available GOAP Actions for Supabase

```typescript
// Database Actions
Action: create_table
  Preconditions: { mcp_connected: true }
  Effects: { table_exists: true }
  Cost: 2
  MCP_Tool: "mcp__supabase__query"

Action: add_rls_policy
  Preconditions: { table_exists: true }
  Effects: { rls_active: true }
  Cost: 3
  MCP_Tool: "mcp__supabase__query"

Action: create_index
  Preconditions: { table_exists: true }
  Effects: { query_optimized: true }
  Cost: 2
  MCP_Tool: "mcp__supabase__query"

// Storage Actions
Action: create_storage_bucket
  Preconditions: { mcp_connected: true }
  Effects: { storage_available: true }
  Cost: 2
  MCP_Tool: "mcp__supabase__storage"

Action: configure_bucket_policies
  Preconditions: { storage_available: true }
  Effects: { storage_secured: true }
  Cost: 3
  MCP_Tool: "mcp__supabase__storage"

// Auth Actions
Action: enable_auth_provider
  Preconditions: { mcp_connected: true }
  Effects: { auth_provider_active: true }
  Cost: 2
  MCP_Tool: "mcp__supabase__auth"

Action: configure_auth_policies
  Preconditions: { auth_provider_active: true }
  Effects: { auth_secured: true }
  Cost: 3
  MCP_Tool: "mcp__supabase__auth"

// Realtime Actions
Action: enable_realtime
  Preconditions: { table_exists: true }
  Effects: { realtime_active: true }
  Cost: 2
  MCP_Tool: "mcp__supabase__realtime"
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Supabase Migration

on:
  push:
    branches: [main]
    paths:
      - 'supabase/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Supabase CLI
        run: npm install -g supabase

      - name: Run Migrations
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          SUPABASE_PROJECT_ID: ${{ secrets.SUPABASE_PROJECT_ID }}
        run: |
          supabase db push
```

---

## Custom MCP Server Configuration

### Advanced Claude Config

Edit `~/.claude.json` for advanced configuration:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["@supabase/mcp-server-supabase"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_ANON_KEY": "your-anon-key",
        "SUPABASE_ACCESS_TOKEN": "sbp_your-token",
        "LOG_LEVEL": "debug",
        "TIMEOUT": "30000"
      }
    }
  }
}
```

---

## Performance Optimization

### Connection Pooling

For high-traffic applications:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    db: {
      schema: 'public',
    },
    auth: {
      autoRefreshToken: true,
      persistSession: false
    },
    global: {
      headers: {
        'x-connection-pool': 'enabled'
      }
    }
  }
)
```

### Query Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- Use prepared statements
PREPARE get_user AS
  SELECT * FROM users WHERE id = $1;
```

---

## Security Best Practices

### 1. Token Rotation

Rotate your Personal Access Token regularly:

```bash
# Script: rotate-token.sh
#!/bin/bash

echo "Rotating Supabase PAT..."

# Generate new token in dashboard first
read -p "Enter new PAT: " NEW_TOKEN

# Update .env
sed -i "s/SUPABASE_ACCESS_TOKEN=.*/SUPABASE_ACCESS_TOKEN=$NEW_TOKEN/" .env

# Reinstall MCP
claude mcp remove supabase
source .env
claude mcp add supabase npx @supabase/mcp-server-supabase \
  --env SUPABASE_URL="$SUPABASE_URL" \
  --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN"

echo "Token rotated successfully!"
```

### 2. RLS Policies

Always enable Row Level Security:

```sql
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own data
CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Policy: Users can update their own data
CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  USING (auth.uid() = id);
```

### 3. Environment-Specific Keys

```bash
# Production: Use service_role with restrictions
SUPABASE_SERVICE_ROLE_KEY=your-restricted-service-role-key

# Development: Use service_role with full access
SUPABASE_SERVICE_ROLE_KEY=your-full-access-service-role-key

# Never use service_role on client-side!
# Client should only use ANON_KEY
```

---

## Monitoring and Logging

### Enable Debug Logging

```bash
# Add to .env
LOG_LEVEL=debug
MCP_DEBUG=true

# Reinstall MCP with debug enabled
claude mcp remove supabase
claude mcp add supabase npx @supabase/mcp-server-supabase \
  --env SUPABASE_URL="$SUPABASE_URL" \
  --env SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  --env SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN" \
  --env LOG_LEVEL="debug"
```

### View Logs

```bash
# Claude Code MCP logs
tail -f ~/.claude/logs/mcp-servers.log

# Filter for Supabase
tail -f ~/.claude/logs/mcp-servers.log | grep supabase
```

---

## Database Migrations

### Using Supabase CLI with MCP

```bash
# Initialize migrations
npx supabase init

# Create new migration
npx supabase migration new create_users_table

# Edit migration file
# supabase/migrations/20250101000000_create_users_table.sql

# Apply migration
npx supabase db push

# Reset database (development only!)
npx supabase db reset
```

---

## Testing

### Integration Testing with Supabase

```typescript
// test/supabase.test.ts
import { createClient } from '@supabase/supabase-js'

describe('Supabase Integration', () => {
  let supabase: any

  beforeAll(() => {
    supabase = createClient(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    )
  })

  test('can connect to Supabase', async () => {
    const { data, error } = await supabase
      .from('users')
      .select('count')

    expect(error).toBeNull()
    expect(data).toBeDefined()
  })

  test('RLS policies work correctly', async () => {
    // Test with anon key
    const anonClient = createClient(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_ANON_KEY!
    )

    const { data, error } = await anonClient
      .from('users')
      .select('*')

    // Should not return other users' data
    expect(data).toHaveLength(0)
  })
})
```

---

## Resources

- [Supabase MCP Package](https://www.npmjs.com/package/@supabase/mcp-server-supabase)
- [Supabase Docs](https://supabase.com/docs)
- [Claude Flow GOAP](https://github.com/ruvnet/claude-flow)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

---

**Last Updated:** October 31, 2025

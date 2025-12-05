# HeroForge.AI Course: AI-Powered Software Development 
## Lesson 3 Workshop: Skills, Subagents, Hooks & DocuMind Foundation

**Estimated Time:** 45-60 minutes\
**Difficulty:** Intermediate\
**Prerequisites:** Completed Sessions 1-2 (Agentic Engineering fundamentals, Claude Code CLI)

---

## Pre-Workshop Setup (REQUIRED)

### Complete the DocuMind Setup Guide First!

Before starting this workshop, you MUST complete the **S3-Documind-setup-guide.md** which walks you through:

1. **Fork the student repository:** https://github.com/mamd69/heroforge-documind
2. **Launch GitHub Codespace** from your fork
3. **Install Claude Code** (`npm install -g @anthropic-ai/claude-code`)
4. **Install Dialogue Reporter** (`npx dialogue-reporter install`)
5. **Initialize Claude Code** (run `/init` inside Claude Code session)
6. **Configure API keys** (Anthropic, OpenAI)
7. **Verify your environment**

**All workshop exercises assume you are working in your forked `heroforge-documind` Codespace.**

If you haven't completed the setup guide, stop now and complete it first. The workshop won't work properly without the correct environment.

---

### Quick Verification

In your **heroforge-documind Codespace**, run these commands to verify you're ready:

```bash
# Verify you're in the right repo
pwd
# Expected: /workspaces/heroforge-documind

# Verify Claude Code
claude --version

# Verify Dialogue Reporter hooks
ls .claude/hooks/
# Should show dialogue reporter files

# Verify Claude Code was initialized
ls .claude/
# Should show CLAUDE.md and other config files

# Or verify CLAUDE.md exists
cat CLAUDE.md 2>/dev/null && echo "✅ Claude Code initialized" || echo "❌ Run /init inside Claude Code"

# Verify API key is set
echo $ANTHROPIC_API_KEY
# Should show sk-ant-xxxxx
```

**All checks pass?** You're ready to start the workshop!

---

## Workshop Objectives

By completing this workshop, you will:
- [x] Understand the difference between Personal and Project Skills
- [x] Create a custom Claude Skill for document processing
- [x] Build a Subagent with specialized knowledge for code review
- [x] Implement pre-task and post-task hooks for automation
- [x] Start building the DocuMind foundation (file upload & basic processing)
- [x] Apply the skill/subagent/hook architecture to a real application

---

## Git Workflow Basics (5 minutes)

### Concept: Version Control for AI Development

When building AI systems like DocuMind, version control is essential for:
- **Tracking experiments:** "Which prompt worked better?"
- **Collaboration:** Multiple developers working on different features
- **Rollback capability:** Undo changes that broke the system
- **Code review:** Get feedback before merging changes

### Exercise 0.1: Set Up Your Development Branch

**Task:** Create a feature branch for document processing work.

**Step 1: Create a GitHub Issue (2 mins)**

Go to your GitHub repository and create an issue:
```
Title: Implement document processing pipeline
Labels: feature, session-3
Description:
- Create multi-agent document processing architecture
- Implement ClaudeFlow swarm coordination
- Add semantic chunking and embedding generation
- Test pipeline with sample documents
```

Note the issue number (e.g., #12)

**Step 2: Create Feature Branch (1 min)**

```bash
# Check current branch
git branch
# Should show: * main

# Create feature branch from issue
git checkout -b issue-12-document-processing

# Verify you're on the new branch
git branch
# Should show: * issue-12-document-processing
```

**Branch Naming Convention:**
- Format: `issue-<number>-<short-description>`
- Example: `issue-12-document-processing`
- Use hyphens, lowercase, keep under 50 characters

**Step 3: Configure Git (if first time) (2 mins)**

```bash
# Set your name and email (if not already configured)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list | grep user
```

### When to Commit

Throughout this workshop, commit your work at these milestones:
1. **After Exercise 1.1:** Architecture design complete
2. **After Exercise 2.2:** ClaudeFlow agents spawned
3. **After Exercise 3.1:** Pipeline coordinator implemented
4. **After Module 4:** Challenge complete

### Commit Message Guidelines

Use this format:
```
<type>: <short summary (50 chars or less)>

<optional detailed description>

Closes #<issue-number>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Adding tests
- `refactor:` Code restructuring

**Examples:**
```bash
# Good commit message
git commit -m "feat: implement ClaudeFlow multi-agent coordinator

- Add PipelineCoordinator class with async document processing
- Implement parallel execution with asyncio.gather
- Add error recovery with exponential backoff
- Track processing metrics per document

Closes #12"

# Bad commit messages (avoid these)
git commit -m "updates"
git commit -m "fixed stuff"
git commit -m "wip"
```

**Quick Commit Flow:**

```bash
# 1. Check what changed
git status

# 2. Add files (be selective!)
git add src/documind/pipeline_coordinator.py

# 3. Commit with clear message
git commit -m "feat: add pipeline coordinator for document processing

Implements parallel document processing with ClaudeFlow agents.
Includes error handling and performance metrics.

Closes #12"

# 4. View your commit history
git log --oneline -5
```

**Pro Tip:** Commit small, logical units of work. Each commit should represent one complete idea.

---

## Planning Your Work with GitHub Issues (5 minutes)

### Concept: Issue-Driven Development

Professional developers don't just start coding. They plan work using **GitHub Issues**:

**Benefits:**
- 📋 **Clear requirements** - Document what to build before building it
- 💬 **Discussion space** - Get feedback from teammates before coding
- 📊 **Progress tracking** - See what's done, in progress, and todo
- 🔗 **Traceability** - Link commits and PRs to original requirements
- 📚 **Documentation** - History of decisions and rationale

**When to create an issue:**
- ✅ Before starting a new feature
- ✅ When you find a bug
- ✅ For improvements or optimizations
- ✅ For questions or discussion

### Issue-Driven Workflow

```
1. Create Issue → Document what to build (#12)
2. Discuss → Get feedback from team/instructor
3. Break Down → Add checkboxes for sub-tasks
4. Create Branch → git checkout -b issue-12-feature
5. Implement → Write code
6. Commit → Reference issue: "Closes #12"
7. Create PR → Links to issue automatically
8. Review → Discuss in PR
9. Merge → Issue auto-closes
10. Celebrate → Feature complete! 🎉
```

### Best Practices

**DO:**
- ✅ Create issue BEFORE starting work
- ✅ Write clear, specific requirements
- ✅ Add acceptance criteria (how to know it's done)
- ✅ Reference issues in commits: `git commit -m "feat: add feature (Closes #12)"`
- ✅ Close issues when work is merged

**DON'T:**
- ❌ Start coding without an issue
- ❌ Create vague issues: "Improve the thing"
- ❌ Forget to close issues (leads to zombie issues)
- ❌ Put code in issues (use gists/branches instead)

Now you're ready to implement the feature tracked by this issue! 🚀

---

## Module 1: Understanding Skills (15 minutes)

### Concept Review

**What is a Claude Skill?**

A Claude Skill is a reusable, shareable instruction set that gives Claude specialized capabilities. Think of it as a "knowledge module" or "expert persona" that can be invoked on-demand.

**Types of Skills:**
1. **Personal Skills** (`~/.claude/skills/`) - Available across all your projects
2. **Project Skills** (`.claude/skills/`) - Specific to one repository/project

**Skills vs. Regular Prompts:**
- **Regular Prompt**: One-off instruction ("Write a Python function...")
- **Skill**: Reusable expert system ("You are a Python testing expert. When asked to test code, you follow these rules...")

**Skill Structure:**
```markdown
# Skill Name

Brief description

## Usage
When to invoke this skill

## Rules
1. Rule one
2. Rule two

## Example
Example invocation
```

---

### Exercise 1.1: Create Your First Skill - Document Parser Expert

**Task:** Create a skill that makes Claude an expert at parsing and extracting information from documents.

**Instructions:**

**Step 1: Create the Skill File (3 mins)**

In your Codespace terminal:
```bash
# Create project skills directory
mkdir -p .claude/skills

# Create the skill file
touch .claude/skills/document-parser.md
```

**Step 2: Write the Skill Definition (7 mins)**

Open `.claude/skills/document-parser.md` and add:

```markdown
# Document Parser Expert

You are an expert at parsing, analyzing, and extracting structured information from documents.

## Usage
Invoke this skill when working with document processing, text extraction, or content analysis.

## Rules
1. Always identify the document type first (PDF, Markdown, text, etc.)
2. Extract key metadata (title, author, date, sections)
3. Create structured summaries with clear hierarchies
4. Identify and extract key entities (names, dates, locations, concepts)
5. Preserve important formatting and structure
6. Flag any ambiguous or unclear content
7. Output in clean, parseable JSON or Markdown format

## Output Format
For each document analyzed:
- **Metadata**: Type, size, creation date
- **Structure**: Sections, headings, hierarchy
- **Key Entities**: People, places, dates, concepts
- **Summary**: 2-3 sentence overview
- **Action Items**: Extracted tasks or next steps (if any)

## Example
Input: "Analyze this meeting notes document"
Output:
```json
{
  "metadata": {
    "type": "Meeting Notes",
    "date": "2025-11-24",
    "participants": ["Alice", "Bob"]
  },
  "structure": {
    "sections": ["Agenda", "Discussion", "Action Items"]
  },
  "key_entities": {
    "people": ["Alice", "Bob"],
    "topics": ["Q4 Planning", "Budget Review"]
  },
  "summary": "Team meeting discussing Q4 planning and budget allocation.",
  "action_items": [
    "Alice: Submit budget proposal by Friday",
    "Bob: Schedule follow-up meeting"
  ]
}
```
```

**Step 3: Test the Skill (5 mins)**

In your Claude Code terminal (`dsp`), type:
```
/skill document-parser

Analyze this text: "Project Update - November 24, 2025. Team leads discussed the DocuMind implementation timeline. Sarah will complete the database schema by Monday. John will write integration tests. Next meeting: December 1st."
```

**Expected Outcome:**
Claude should respond using the structured JSON format defined in your skill, extracting participants, dates, and action items.

---

**🔄 Git Checkpoint**

Commit your progress:

```bash
git add .claude/skills/document-parser.md
git commit -m "feat: create document parser skill

- Add document parser expert skill with structured output format
- Define metadata extraction and entity recognition rules
- Include JSON output template for consistent analysis

Relates to #12"
```

---

### Quiz 1:

**Question 1:** What is the difference between Personal and Project skills?

   a) Personal skills are stored in your home directory and available everywhere; Project skills are in `.claude/skills/` and specific to one repository\
   b) Personal skills are free; Project skills cost money\
   c) Personal skills use Python; Project skills use JavaScript\
   d) There is no difference

**Question 2:** When should you create a skill instead of just writing a prompt?\
   a) When you need the same expert behavior across multiple conversations or projects\
   b) When you want to write less than 10 words\
   c) Skills are always better than prompts in every situation\
   d) Only when working with Python code

**Question 3:** What goes in the "Rules" section of a skill definition?\
   a) The specific behaviors and constraints Claude should follow when using this skill\
   b) Legal terms and conditions\
   c) Database connection strings\
   d) Your API keys

**Answers:**
1. **a)** Personal skills (~/.claude/skills/) are globally available; Project skills (.claude/skills/) are repository-specific
2. **a)** Skills are best for reusable expert behaviors you'll need repeatedly
3. **a)** Rules define the specific behaviors and constraints for the skill

---

## Module 2: Building Subagents (15 minutes)

### Concept Review

**What is a Subagent?**

A Subagent is a specialized AI agent that Claude can spawn to handle specific tasks. While Skills give Claude expertise, Subagents allow Claude to *delegate* work to separate, focused agents.

**Skills vs. Subagents:**
| Feature | Skill | Subagent |
|---------|-------|----------|
| **What it is** | Knowledge module | Separate agent instance |
| **How it works** | Claude uses the skill's rules | Claude spawns independent agent |
| **Best for** | Adding expertise | Delegating complex subtasks |
| **Example** | "Document parser expert" | "Code reviewer that checks security" |

**Subagent Structure:**
```yaml
name: subagent-name
role: What this agent does
expertise: Specific knowledge domain
tools: Available tools/capabilities
constraints: Limitations and rules
```

---

### Exercise 2.1: Create a Code Review Subagent

**Task:** Build a subagent that specializes in security-focused code review.

**Instructions:**

**Step 1: Create Subagent Directory (2 mins)**

```bash
mkdir -p .claude/subagents
touch .claude/subagents/security-reviewer.md
```

**Step 2: Define the Subagent (8 mins)**

Open `.claude/subagents/security-reviewer.md`:

```markdown
# Security Review Subagent

## Role
Expert security-focused code reviewer specializing in identifying vulnerabilities, security anti-patterns, and compliance issues.

## Expertise
- OWASP Top 10 vulnerabilities
- Secure coding practices (Python, JavaScript, SQL)
- Authentication & authorization patterns
- Data validation and sanitization
- Secret management
- SQL injection prevention
- XSS prevention
- CSRF protection

## Review Checklist
When reviewing code, ALWAYS check:

### Input Validation
- [ ] All user inputs validated before use
- [ ] Type checking enforced
- [ ] Length limits applied
- [ ] Special characters sanitized

### Authentication & Authorization
- [ ] Authentication required for sensitive operations
- [ ] Authorization checks present
- [ ] Session management secure
- [ ] Password handling follows best practices

### Data Protection
- [ ] No hardcoded secrets or API keys
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced for data in transit
- [ ] Database queries parameterized (no string concatenation)

### Error Handling
- [ ] No sensitive information in error messages
- [ ] Proper exception handling
- [ ] Logging doesn't expose secrets

### Dependencies
- [ ] No known vulnerable dependencies
- [ ] Dependencies from trusted sources

## Output Format
Provide security review in this structure:

### Summary
- Overall security rating: HIGH RISK / MEDIUM RISK / LOW RISK / SECURE
- Critical issues: [count]
- Warnings: [count]

### Critical Issues 🚨
[List any immediate security vulnerabilities that must be fixed]

### Warnings ⚠️
[List security concerns that should be addressed]

### Recommendations ✅
[List best practice improvements]

### Approved Items ✓
[List security controls that are correctly implemented]

## Example Review
```python
# Code being reviewed:
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result
```

**Security Review:**

### Summary
- Overall security rating: **HIGH RISK** 🚨
- Critical issues: 2
- Warnings: 1

### Critical Issues 🚨
1. **SQL Injection Vulnerability**: Query uses string concatenation instead of parameterized queries. An attacker can inject SQL code through the username/password fields.
   ```python
   # Attack example: username = "admin' --"
   # Results in: SELECT * FROM users WHERE username='admin' --' AND password='...'
   ```

2. **Plaintext Password Storage**: Password appears to be stored/compared in plaintext. Passwords must be hashed (bcrypt, argon2).

### Warnings ⚠️
1. No rate limiting visible - vulnerable to brute force attacks

### Recommendations ✅
```python
# Secure implementation:
from passlib.hash import bcrypt
from sqlalchemy import text

def login(username, password):
    # Use parameterized query
    query = text("SELECT * FROM users WHERE username = :username")
    result = db.execute(query, {"username": username}).fetchone()

    if result and bcrypt.verify(password, result.password_hash):
        return result
    return None
```
```

**Step 3: Invoke the Subagent (5 mins)**

In Claude Code terminal:
```
/subagent security-reviewer

Review this code for security issues:

```python
def upload_file(filename, content):
    path = f"/uploads/{filename}"
    with open(path, 'w') as f:
        f.write(content)
    return path
```
```

**Expected Outcome:**
The subagent should identify:
- Path traversal vulnerability (filename not sanitized)
- No file type validation
- No size limits
- Arbitrary file write capability

---

### Exercise 2.2: Create a Documentation Subagent

**Challenge (Optional Advanced Task):**

Create a subagent called `.claude/subagents/doc-writer.md` that:
- Generates comprehensive documentation for code
- Follows JSDoc or Python docstring standards
- Creates README files with usage examples
- Identifies undocumented functions

Test it on your DocuMind code from the demo!

---

**🔄 Git Checkpoint**

Commit your progress:

```bash
git add .claude/subagents/security-reviewer.md
git commit -m "feat: add security review subagent

- Create specialized security reviewer with OWASP checklist
- Implement vulnerability detection for SQL injection and path traversal
- Add structured output format with risk ratings

Relates to #12"
```

---

### Quiz 2:

**Question 1:** What is the primary difference between a Skill and a Subagent?\
   a) Skills provide expertise to Claude; Subagents are separate agents Claude delegates work to\
   b) Skills are written in YAML; Subagents are written in JSON\
   c) Skills are faster than Subagents\
   d) Subagents can only review code

**Question 2:** When should you use a Subagent instead of a Skill?\
   a) When the task is complex enough to warrant a separate, focused agent with its own context\
   b) When you want to save money\
   c) Only on Tuesdays\
   d) Whenever you write Python code

**Question 3:** In the security reviewer subagent, what does the checklist accomplish?\
   a) It ensures the subagent systematically checks for specific security issues every time\
   b) It makes the subagent slower\
   c) It's just for decoration\
   d) It replaces the need for actual code review

**Answers:**
1. **a)** Skills = expertise for Claude; Subagents = separate specialized agents
2. **a)** Use subagents for complex, focused tasks that benefit from isolated context
3. **a)** Checklists ensure systematic, repeatable security analysis

---

## Module 3: Implementing Hooks (15 minutes)

### Concept Review

**What are Hooks?**

Hooks are automation scripts that run automatically at specific points in your workflow:
- **Pre-task hooks**: Run *before* Claude starts a task (setup, validation)
- **Post-task hooks**: Run *after* Claude completes a task (formatting, testing, deployment)

**Hook Types in Claude Flow:**
1. `pre-task` - Before task execution
2. `post-task` - After task completion
3. `pre-edit` - Before file editing
4. `post-edit` - After file editing
5. `session-start` - When Claude session begins
6. `session-end` - When Claude session ends

**Why Use Hooks?**
- Automate repetitive tasks (formatting, linting, testing)
- Enforce quality standards automatically
- Create audit trails
- Coordinate with other systems (git, databases, APIs)

---

### Exercise 3.1: Create a Pre-Task Hook

**Task:** Create a hook that runs before every task to validate the environment.

**Instructions:**

**Step 1: Create Hooks Directory (2 mins)**

```bash
mkdir -p .claude/hooks
touch .claude/hooks/pre-task-validator.sh
chmod +x .claude/hooks/pre-task-validator.sh
```

**Step 2: Write the Hook Script (5 mins)**

Open `.claude/hooks/pre-task-validator.sh`:

```bash
#!/bin/bash
# Pre-Task Validation Hook
# Runs before Claude executes any task

echo "🔍 Pre-Task Validator Running..."
echo ""

# Check 1: Verify we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ ERROR: Not in project root directory"
    exit 1
fi
echo "✅ In project root directory"

# Check 2: Verify required directories exist
required_dirs=(".claude" "docs" "src")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "⚠️  WARNING: $dir directory missing - creating..."
        mkdir -p "$dir"
    else
        echo "✅ $dir directory exists"
    fi
done

# Check 3: Verify .env file exists (if .env.example exists)
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env.example exists but .env missing"
    echo "   Run: cp .env.example .env"
fi

# Check 4: Verify git status is clean (optional warning)
if command -v git &> /dev/null; then
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  WARNING: Uncommitted changes detected"
        echo "   Files changed: $(git status --short | wc -l)"
    else
        echo "✅ Git working tree clean"
    fi
fi

# Check 5: Log the task start
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
echo "$timestamp - Pre-task validation completed" >> .claude/hooks/task.log

echo ""
echo "✅ Pre-task validation complete - ready to proceed"
```

---

**🔄 Git Checkpoint**

Commit your progress:

```bash
git add .claude/hooks/pre-task-validator.sh .claude/hooks/config.json
git commit -m "feat: implement pre-task validation hook

- Add environment validation checks (directories, dependencies)
- Check git status and working tree cleanliness
- Log task execution for audit trail

Relates to #12"
```

---

**Step 3: Register the Hook (3 mins)**

Create `.claude/hooks/config.json`:

```json
{
  "hooks": {
    "pre-task": [
      {
        "name": "Environment Validator",
        "script": ".claude/hooks/pre-task-validator.sh",
        "enabled": true
      }
    ],
    "post-task": [],
    "pre-edit": [],
    "post-edit": []
  },
  "settings": {
    "stopOnError": true,
    "logLevel": "info"
  }
}
```

**Step 4: Test the Hook (5 mins)**

```bash
# Test the hook manually
./.claude/hooks/pre-task-validator.sh

# Expected output:
# 🔍 Pre-Task Validator Running...
# ✅ In project root directory
# ✅ .claude directory exists
# ✅ docs directory exists
# ✅ src directory exists
# ✅ Git working tree clean
# ✅ Pre-task validation complete
```

---

### Exercise 3.2: Create a Post-Edit Hook for Auto-Formatting

**Task:** Create a hook that automatically formats code after Claude edits a file.

**Instructions:**

**Step 1: Create the Hook Script (5 mins)**

```bash
touch .claude/hooks/post-edit-formatter.sh
chmod +x .claude/hooks/post-edit-formatter.sh
```

Open `.claude/hooks/post-edit-formatter.sh`:

```bash
#!/bin/bash
# Post-Edit Auto-Formatter Hook
# Runs after Claude edits a file

FILE=$1  # File that was edited (passed by Claude)

if [ -z "$FILE" ]; then
    echo "❌ No file specified"
    exit 1
fi

echo "🎨 Auto-formatting $FILE..."

# Determine file type and format accordingly
case "$FILE" in
    *.py)
        # Python: Use black (if available)
        if command -v black &> /dev/null; then
            black "$FILE" --quiet
            echo "✅ Python formatted with black"
        else
            echo "⚠️  black not installed - skipping Python formatting"
        fi
        ;;

    *.js|*.jsx)
        # JavaScript: Use prettier (if available)
        if command -v prettier &> /dev/null; then
            prettier --write "$FILE" > /dev/null 2>&1
            echo "✅ JavaScript formatted with prettier"
        else
            echo "⚠️  prettier not installed - skipping JS formatting"
        fi
        ;;

    *.md)
        # Markdown: Basic cleanup (trailing spaces)
        sed -i 's/[[:space:]]*$//' "$FILE"
        echo "✅ Markdown cleaned (trailing spaces removed)"
        ;;

    *)
        echo "ℹ️  No formatter configured for this file type"
        ;;
esac

# Log the formatting action
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
echo "$timestamp - Formatted $FILE" >> .claude/hooks/format.log

exit 0
```

**Step 2: Update Hook Configuration**

Update `.claude/hooks/config.json`:

```json
{
  "hooks": {
    "pre-task": [
      {
        "name": "Environment Validator",
        "script": ".claude/hooks/pre-task-validator.sh",
        "enabled": true
      }
    ],
    "post-task": [],
    "pre-edit": [],
    "post-edit": [
      {
        "name": "Auto Formatter",
        "script": ".claude/hooks/post-edit-formatter.sh",
        "enabled": true,
        "passFileArgument": true
      }
    ]
  },
  "settings": {
    "stopOnError": false,
    "logLevel": "info"
  }
}
```

**Step 3: Test the Hook**

```bash
# Create a messy Python file
cat > test.py << 'EOF'
def hello(  ):
    print( "Hello World"  )
    return   True
EOF

# Run the hook
./.claude/hooks/post-edit-formatter.sh test.py

# Check if formatted (should have proper spacing)
cat test.py
```

---

### Quiz 3:

**Question 1:** What is the purpose of a pre-task hook?\
   a) To run validation, setup, or preparation before Claude executes a task\
   b) To delete files after a task\
   c) To slow down Claude\
   d) To replace Claude entirely

**Question 2:** Why would you use a post-edit hook for formatting instead of asking Claude to format?\
   a) Automation ensures consistency and saves tokens; Claude doesn't need to think about formatting\
   b) Hooks are faster than Claude\
   c) It's impossible to ask Claude to format code\
   d) Post-edit hooks are required by law

**Question 3:** In the post-edit-formatter hook, what does `FILE=$1` mean?\
   a) It captures the first argument (the file path) passed to the script\
   b) It sets the file to be named "1"\
   c) It's a syntax error\
   d) It deletes the first file in the directory

**Answers:**
1. **a)** Pre-task hooks run setup/validation before task execution
2. **a)** Hooks automate formatting consistently, saving Claude's attention for logic
3. **a)** `$1` captures the first command-line argument (the file path)

---

## Module 4: Challenge Project - Mini DocuMind (15 minutes)

### Challenge Overview

Build a simplified version of DocuMind that demonstrates Skills, Subagents, and Hooks working together.

**Your Mission:**
Create a document processing pipeline that:
1. Uses a Skill to analyze uploaded documents
2. Uses a Subagent to validate document security
3. Uses Hooks to automate the workflow

---

### Challenge Requirements

**Feature:** Document Upload & Analysis Pipeline

**What to Build:**

1. **Document Upload Function** (Python)
   - Accept file path as input
   - Read file contents
   - Return document metadata

2. **Use the Document Parser Skill**
   - Invoke your document-parser skill from Module 1
   - Extract structured information from the document

3. **Security Review via Subagent**
   - Use your security-reviewer subagent to check for:
     - Path traversal risks
     - File type validation
     - Content security issues

4. **Automated Hooks**
   - Pre-task hook validates environment
   - Post-task hook logs the analysis results

---

### Starter Code

Create `src/documind/upload_handler.py`:

```python
"""
DocuMind Document Upload Handler
Demonstrates Skills, Subagents, and Hooks integration
"""
import os
import json
from datetime import datetime
from pathlib import Path

def validate_file_path(file_path):
    """
    Validates that file path is safe and exists.

    TODO: Add security validation
    - Check for path traversal attempts
    - Validate file extension
    - Check file size limits
    """
    # Your code here
    pass

def read_document(file_path):
    """
    Reads document contents safely.

    TODO: Implement safe file reading
    - Open file in read mode
    - Handle different encodings
    - Return contents as string
    """
    # Your code here
    pass

def extract_metadata(file_path, contents):
    """
    Extracts metadata from document.

    TODO: Extract:
    - File name
    - File size
    - Created date
    - Modified date
    - Number of lines/words
    """
    # Your code here
    pass

def analyze_document(file_path):
    """
    Main function: orchestrates document analysis.

    This function should:
    1. Validate the file path (security)
    2. Read the document
    3. Extract metadata
    4. Return structured analysis

    TODO: Implement full pipeline
    """
    # Your code here
    pass

# Test the function
if __name__ == "__main__":
    # Create a sample document for testing
    test_doc = "test_document.txt"
    with open(test_doc, 'w') as f:
        f.write("Sample document for DocuMind testing.\nThis is line 2.")

    # Analyze it
    result = analyze_document(test_doc)
    print(json.dumps(result, indent=2))
```

---

### Your Task

**Step 1: Implement the Functions (10 mins)**

Using Claude Code with your skills and subagents:

1. Open `dsp` (Claude Code CLI)
2. Invoke your document-parser skill:
   ```
   /skill document-parser

   Complete the implementation of src/documind/upload_handler.py.

   Requirements:
   - validate_file_path: Check for "../" path traversal, validate extensions (.txt, .md, .pdf)
   - read_document: Safely read file contents, handle UTF-8 encoding
   - extract_metadata: Get file size, dates, word/line count
   - analyze_document: Orchestrate the full pipeline, return JSON
   ```

3. After implementation, invoke your security subagent:
   ```
   /subagent security-reviewer

   Review src/documind/upload_handler.py for security vulnerabilities.
   ```

4. Fix any security issues identified

**Step 2: Test with Hooks (5 mins)**

```bash
# Run pre-task hook
./.claude/hooks/pre-task-validator.sh

# Test the implementation
python src/documind/upload_handler.py

# Expected output: JSON with metadata
{
  "file": "test_document.txt",
  "size": 67,
  "lines": 2,
  "words": 9,
  "created": "2025-11-24T10:30:00",
  "safe": true
}
```

---

### Success Criteria

Your implementation is complete when:

- [ ] `validate_file_path` prevents path traversal attacks
- [ ] `validate_file_path` only allows .txt, .md, .pdf files
- [ ] `read_document` safely reads file contents
- [ ] `extract_metadata` returns file stats (size, dates, word count)
- [ ] `analyze_document` orchestrates the full pipeline
- [ ] Security subagent finds NO critical issues
- [ ] Pre-task hook passes all checks
- [ ] Test run produces valid JSON output

---

## Answer Key

### Exercise 1.1 Solution

The skill file should be created at `.claude/skills/document-parser.md` with the content provided in the exercise.

To test:
```
/skill document-parser

Analyze this text: "Project Update - November 24, 2025..."
```

Expected output:
```json
{
  "metadata": {
    "type": "Project Update",
    "date": "2025-11-24"
  },
  "key_entities": {
    "people": ["Sarah", "John"],
    "dates": ["Monday", "December 1st"]
  },
  "summary": "DocuMind implementation timeline discussion with assigned tasks.",
  "action_items": [
    "Sarah: Complete database schema by Monday",
    "John: Write integration tests",
    "Team: Next meeting December 1st"
  ]
}
```

---

### Exercise 2.1 Solution

The subagent should be at `.claude/subagents/security-reviewer.md`.

For the upload_file test code, the review should identify:

**Security Review:**

### Summary
- Overall security rating: **HIGH RISK** 🚨
- Critical issues: 2
- Warnings: 1

### Critical Issues 🚨
1. **Path Traversal Vulnerability**: The filename is directly concatenated without sanitization. An attacker can use "../" to write files anywhere on the system.
   ```python
   # Attack: filename = "../../etc/passwd"
   # Results in: /uploads/../../etc/passwd = /etc/passwd
   ```

2. **Arbitrary File Write**: No restrictions on file type, size, or content. Attacker can upload malicious files.

### Warnings ⚠️
1. No authentication check - anyone can upload files

### Recommendations ✅
```python
import os
from pathlib import Path

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.md'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = Path("/uploads").resolve()

def upload_file(filename, content):
    # Sanitize filename
    safe_filename = Path(filename).name
    file_path = (UPLOAD_DIR / safe_filename).resolve()

    # Verify path is within upload directory
    if not str(file_path).startswith(str(UPLOAD_DIR)):
        raise ValueError("Invalid file path")

    # Check extension
    if file_path.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("File type not allowed")

    # Check size
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File too large")

    with open(file_path, 'w') as f:
        f.write(content)

    return str(file_path)
```

---

### Module 4 Challenge Solution

Complete implementation of `src/documind/upload_handler.py`:

```python
"""
DocuMind Document Upload Handler
Demonstrates Skills, Subagents, and Hooks integration
"""
import os
import json
from datetime import datetime
from pathlib import Path

# Security configuration
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BASE_DIR = Path(__file__).parent.parent.parent.resolve()

def validate_file_path(file_path):
    """
    Validates that file path is safe and exists.

    Security checks:
    - Prevents path traversal
    - Validates file extension
    - Checks file size limits
    """
    try:
        # Convert to Path object and resolve
        path = Path(file_path).resolve()

        # Check if file exists
        if not path.exists():
            return False, "File does not exist"

        # Check for path traversal
        # Ensure resolved path is within allowed directory
        if not str(path).startswith(str(BASE_DIR)):
            return False, "Path traversal attempt detected"

        # Validate file extension
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"

        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Max: {MAX_FILE_SIZE} bytes"

        # Check if it's a file (not directory)
        if not path.is_file():
            return False, "Path is not a file"

        return True, "File is valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def read_document(file_path):
    """
    Reads document contents safely.

    Handles:
    - Different encodings (UTF-8, fallback to latin-1)
    - Read errors
    - Returns contents as string
    """
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def extract_metadata(file_path, contents):
    """
    Extracts metadata from document.

    Returns:
    - File name
    - File size (bytes)
    - Created date
    - Modified date
    - Number of lines
    - Number of words
    """
    path = Path(file_path)
    stats = path.stat()

    # Count lines and words
    lines = contents.split('\n')
    line_count = len(lines)
    word_count = sum(len(line.split()) for line in lines)

    metadata = {
        "file_name": path.name,
        "file_path": str(path),
        "file_size_bytes": stats.st_size,
        "file_extension": path.suffix,
        "created_timestamp": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified_timestamp": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "line_count": line_count,
        "word_count": word_count,
        "character_count": len(contents)
    }

    return metadata

def analyze_document(file_path):
    """
    Main function: orchestrates document analysis.

    Pipeline:
    1. Validate the file path (security)
    2. Read the document
    3. Extract metadata
    4. Return structured analysis
    """
    result = {
        "status": "unknown",
        "file": file_path,
        "timestamp": datetime.now().isoformat(),
        "metadata": None,
        "preview": None,
        "error": None
    }

    try:
        # Step 1: Validate file path
        is_valid, message = validate_file_path(file_path)
        if not is_valid:
            result["status"] = "error"
            result["error"] = f"Validation failed: {message}"
            return result

        # Step 2: Read document
        contents = read_document(file_path)

        # Step 3: Extract metadata
        metadata = extract_metadata(file_path, contents)

        # Step 4: Create preview (first 200 characters)
        preview = contents[:200]
        if len(contents) > 200:
            preview += "..."

        # Success
        result["status"] = "success"
        result["metadata"] = metadata
        result["preview"] = preview

        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result

# Test the function
if __name__ == "__main__":
    # Create a sample document for testing
    test_doc = "test_document.txt"
    with open(test_doc, 'w') as f:
        f.write("Sample document for DocuMind testing.\n")
        f.write("This is line 2 with some additional content.\n")
        f.write("Line 3 continues the document with more information.")

    print("=" * 60)
    print("DocuMind Document Analysis Test")
    print("=" * 60)
    print()

    # Analyze it
    result = analyze_document(test_doc)
    print(json.dumps(result, indent=2))

    print()
    print("=" * 60)
    print("Testing Security Validation")
    print("=" * 60)
    print()

    # Test path traversal attempt
    malicious_path = "../../../etc/passwd"
    malicious_result = analyze_document(malicious_path)
    print("Path traversal test:")
    print(json.dumps(malicious_result, indent=2))

    print()

    # Test invalid extension
    invalid_ext = "test.exe"
    with open(invalid_ext, 'w') as f:
        f.write("test")
    invalid_result = analyze_document(invalid_ext)
    print("Invalid extension test:")
    print(json.dumps(invalid_result, indent=2))

    # Cleanup
    os.remove(test_doc)
    if os.path.exists(invalid_ext):
        os.remove(invalid_ext)
```

**Expected Output:**
```json
{
  "status": "success",
  "file": "test_document.txt",
  "timestamp": "2025-11-24T10:30:00.123456",
  "metadata": {
    "file_name": "test_document.txt",
    "file_path": "/workspaces/heroforge-documind/test_document.txt",
    "file_size_bytes": 156,
    "file_extension": ".txt",
    "created_timestamp": "2025-11-24T10:29:55.000000",
    "modified_timestamp": "2025-11-24T10:29:55.000000",
    "line_count": 3,
    "word_count": 18,
    "character_count": 156
  },
  "preview": "Sample document for DocuMind testing.\nThis is line 2 with some additional content.\nLine 3 continues the document with more information."
}
```

**Security Test Results:**
```json
{
  "status": "error",
  "file": "../../../etc/passwd",
  "error": "Validation failed: Path traversal attempt detected"
}
```

---

**🔄 Git Checkpoint**

Commit your progress:

```bash
git add src/documind/upload_handler.py tests/
git commit -m "feat: complete document upload handler with security validation

- Implement secure file path validation with path traversal protection
- Add multi-encoding document reader (UTF-8, latin-1 fallback)
- Extract comprehensive metadata (size, dates, word/line counts)
- Create document analysis pipeline with error handling
- Add security tests for path traversal and invalid extensions

Closes #12"
```

---

## Additional Challenges (Optional)

For students who finish early:

### Challenge 1: Advanced Skill - Code Explainer
Create a skill at `.claude/skills/code-explainer.md` that:
- Analyzes code and explains it line-by-line
- Identifies design patterns used
- Suggests improvements
- Generates beginner-friendly documentation

Test it on the upload_handler.py solution!

### Challenge 2: Testing Subagent
Create `.claude/subagents/test-writer.md` that:
- Generates pytest unit tests
- Ensures 80%+ code coverage
- Creates fixtures and mocks
- Tests both success and failure cases

Use it to create `tests/test_upload_handler.py`!

### Challenge 3: Git Commit Hook
Create `.claude/hooks/post-task-git.sh` that:
- Runs tests before allowing commit
- Auto-generates commit message from changes
- Checks for sensitive data in commits
- Updates CHANGELOG.md automatically

### Challenge 4: Full DocuMind Integration
Extend the upload handler to:
- Support PDF files (use PyPDF2)
- Extract text from PDFs
- Store analysis results in SQLite database
- Create a simple CLI interface

---

## Troubleshooting

### Common Issue 1: Skill Not Loading
**Problem:** `/skill document-parser` returns "Skill not found"

**Solution:**
1. Check file exists: `ls -la .claude/skills/`
2. Verify path is `.claude/skills/document-parser.md`
3. Ensure file has content (not empty)
4. Restart Claude Code session

---

### Common Issue 2: Hook Permission Denied
**Problem:** `bash: ./.claude/hooks/pre-task-validator.sh: Permission denied`

**Solution:**
```bash
chmod +x .claude/hooks/pre-task-validator.sh
chmod +x .claude/hooks/post-edit-formatter.sh
```

---

### Common Issue 3: Subagent Not Activating
**Problem:** Subagent doesn't provide specialized analysis

**Solution:**
1. Ensure file is at `.claude/subagents/[name].md`
2. Include clear "Role" and "Expertise" sections
3. Invoke with `/subagent [name]` exactly
4. Check for YAML frontmatter syntax errors

---

### Common Issue 4: Path Traversal Test Failing
**Problem:** Security test should block "../" but doesn't

**Solution:**
Ensure you're using `Path.resolve()` and checking if the resolved path starts with the base directory:

```python
path = Path(file_path).resolve()
if not str(path).startswith(str(BASE_DIR)):
    return False, "Path traversal detected"
```

---

## 5 Ways to Get Better Results from Claude Code

Before you continue to the next session, internalize these tips:

### 1. Demand proof, not promises
Ask "show me the diff" or "run the tests" — don't accept "I've updated the file" without evidence.

### 2. Break tasks into atomic steps
Instead of "refactor auth," try: "list files touching auth → show current flow → update login function → run tests."

### 3. Use "then verify" as a suffix
"Add the env variable to .env, then cat the file to confirm." Build verification into every request.

### 4. Ask for state before and after
"Show test output, make the fix, show test output again." Clear before/after comparison reveals what changed.

### 5. Be skeptical of "Done!" without artifacts
No terminal output, diff, or file contents? Assume nothing happened. Real completions produce evidence.

> **Core principle:** Treat Claude Code like a junior dev who's eager to please but needs to show their work.

---

## Key Takeaways

By completing this workshop, you've learned:

1. **Skills** provide reusable expertise to Claude for specific domains
2. **Subagents** delegate complex subtasks to specialized agent instances
3. **Hooks** automate workflow steps before/after tasks and edits
4. **Security** must be designed into file handling from the start
5. **DocuMind** foundation demonstrates real-world application architecture

**The Triad Pattern:**
```
Skill (Expertise) + Subagent (Delegation) + Hooks (Automation) = Powerful Workflow
```

---

## Next Session Preview

In **Session 4: Database Integration with Supabase MCP**, we'll:
- Connect DocuMind to a real PostgreSQL database
- Use the Supabase MCP server for database operations
- Implement document storage with metadata
- Create a conversation history table
- Build our first API endpoint

**Preparation:**
1. Create a free Supabase account at supabase.com
2. Keep your `.env` file handy for API keys
3. Review PostgreSQL basics (optional)

See you in Session 4!

---

**Workshop Complete! 🎉**

You've built the foundation of DocuMind with Skills, Subagents, and Hooks. You're ready to integrate real database storage!

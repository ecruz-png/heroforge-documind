# DocuMind Setup Guide

**Student Handout - AI-Powered Software Development with Agentic Engineering**

---

## Welcome!

In this guide, you'll set up your DocuMind development environment in GitHub Codespaces. By the end, you'll have a fully configured workspace ready for the Session 3 workshop.

**Time Required:** 15-20 minutes

**What You'll Accomplish:**
- Fork the DocuMind student repository
- Launch a GitHub Codespace
- Configure your API keys
- Verify your environment is working
- Be ready to start the workshop

---

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] **GitHub account** (free) - [Sign up here](https://github.com/join)
- [ ] **Anthropic API key** (you'll get this in Step 3)
- [ ] **OpenAI API key** (you'll get this in Step 3)
- [ ] Completed Sessions 1 and 2 of the course

---

## Step 1: Fork the Student Repository (5 minutes)

### 1.1 Navigate to the Repository

Go to: **https://github.com/mamd69/heroforge-documind**

### 1.2 Fork the Repository

1. Click the **Fork** button in the top-right corner
2. Select **your personal GitHub account** as the destination
3. Keep the default repository name: `heroforge-documind`
4. Click **Create fork**

### 1.3 Verify Your Fork

After forking, you should see:
- The repository is now under **your username**: `github.com/YOUR-USERNAME/heroforge-documind`
- You can see all the files and folders

**Troubleshooting:**
- If the Fork button is grayed out, make sure you're logged into GitHub
- If you already have a fork, GitHub will take you to it

---

## Step 2: Launch GitHub Codespace (5 minutes)

### 2.1 Open Codespaces

1. In **your forked repository**, click the green **Code** button
2. Select the **Codespaces** tab
3. Click **Create codespace on main**

### 2.2 Wait for Initialization

The Codespace will take 2-3 minutes to set up. During this time, it's:
- Creating a cloud-based development environment
- Installing Node.js and Python
- Installing project dependencies
- Configuring Claude Code CLI

### 2.3 Verify Codespace is Ready

You'll know it's ready when you see:
- VS Code interface in your browser
- File explorer on the left showing project files
- Terminal panel at the bottom
- No loading indicators

**Troubleshooting:**
- If it takes more than 5 minutes, try refreshing the page
- If it fails, click "..." → "Delete codespace" and try again

---

## Step 3: Get Your API Keys (10 minutes)

You'll need two API keys to complete the workshop. Follow these steps to get them.

### 3.1 Anthropic API Key (Required)

The Anthropic API key powers Claude for document analysis.

**Steps:**
1. Go to **[https://console.anthropic.com/](https://console.anthropic.com/)**
2. Sign up for a new account or log in
3. Navigate to **API Keys** in the left sidebar
4. Click **Create Key**
5. Name it: `DocuMind Workshop`
6. Click **Create Key**
7. **Important:** Copy the key immediately (starts with `sk-ant-`)
   - You'll only see it once!
   - Save it somewhere safe (notes app, password manager)

**Cost:** Free tier includes $5 credit - more than enough for the entire course.

### 3.2 OpenAI API Key (Required)

The OpenAI API key is used for text embeddings in later sessions.

**Steps:**
1. Go to **[https://platform.openai.com/](https://platform.openai.com/)**
2. Sign up for a new account or log in
3. Navigate to **API Keys** (click your profile → View API Keys)
4. Click **Create new secret key**
5. Name it: `DocuMind Embeddings`
6. Copy the key (starts with `sk-`)
   - Save it with your Anthropic key

**Cost:** Pay-as-you-go, but embeddings are very cheap (~$0.01 for the entire workshop).

### 3.3 OpenRouter API Key (Optional)

OpenRouter provides access to multiple AI models (GPT-4, Gemini, etc.). You can skip this for now and add it later in Session 6.

**If you want to set it up now:**
1. Go to **[https://openrouter.ai/](https://openrouter.ai/)**
2. Sign up with GitHub
3. Navigate to **Keys**
4. Create a new key
5. Copy the key (starts with `sk-or-`)

### 3.4 Supabase Credentials (For Session 4+)

You don't need Supabase yet. We'll set this up together at the start of Session 4.

---

## Step 4: Configure Environment Variables (5 minutes)

### 4.1 What Are Environment Variables?

Environment variables are a secure way to store sensitive information like API keys:
- They're stored in a `.env` file
- This file is NOT committed to Git (protected by `.gitignore`)
- Your code reads them at runtime

### Why `.env` Files (Not Codespace Secrets)?

GitHub Codespaces offers "Secrets" as an alternative, but we use `.env` files because:

| `.env` Files | Codespace Secrets |
|--------------|-------------------|
| Industry standard practice | GitHub-specific feature |
| Works locally, in Docker, in production | Only works in Codespaces |
| You can see and debug your keys | Keys are hidden from view |
| Transferable skill you'll use everywhere | Less common in real projects |
| Easier to troubleshoot | Harder to debug issues |

Learning to use `.env` files properly is an essential developer skill!

### 4.2 Create Your .env File

In your Codespace terminal (bottom panel), run:

```bash
# Copy the example file to create your .env
cp .env.example .env
```

### 4.3 Add Your API Keys

Open the `.env` file:
- Click on `.env` in the file explorer (left panel), OR
- Run: `code .env` in the terminal

Replace the placeholder values with your actual keys:

```bash
# Required for Claude Code (Session 3+)
ANTHROPIC_API_KEY=sk-ant-YOUR_ACTUAL_KEY_HERE

# Required for embeddings (Session 5+)
OPENAI_API_KEY=sk-YOUR_ACTUAL_KEY_HERE

# Optional for multi-model access (Session 6+)
OPENROUTER_API_KEY=sk-or-YOUR_ACTUAL_KEY_HERE
```

### 4.4 Save the File

Press **Cmd+S** (Mac) or **Ctrl+S** (Windows/Linux)

### 4.5 Common Mistakes to Avoid

| Wrong | Correct |
|-------|---------|
| `ANTHROPIC_API_KEY="sk-ant-123"` | `ANTHROPIC_API_KEY=sk-ant-123` |
| `KEY = value` | `KEY=value` |
| Committing `.env` to Git | `.env` stays local only |

**Security Reminder:** Never share your `.env` file or paste your API keys in public places like GitHub Issues or Discord.

### 4.6 Verify Environment Variables

Test that your variables are loaded:

```bash
# In the terminal, run:
source .env
echo $ANTHROPIC_API_KEY

# You should see your key printed (sk-ant-xxxxx)
```

---

## Step 5: Verify Your Installation (5 minutes)

Run these commands in your terminal to verify everything is set up correctly:

### 5.1 Check Node.js

```bash
node --version
# Expected output: v20.x.x
```

### 5.2 Check Python

```bash
python --version
# Expected output: Python 3.10.x or higher
```

### 5.3 Install Dependencies

```bash
npm install
# Should complete without errors
```

### 5.4 Run Tests

```bash
npm test
# Expected: All tests passing
```

### 5.5 Test Claude Code CLI

```bash
dsp --version
# Expected: Claude Code version number
```

**Troubleshooting:**
- `dsp: command not found` → Run `source ~/.bashrc` and try again
- npm install errors → Try `rm -rf node_modules && npm install`
- Tests failing → Check your `.env` file format

---

## Step 6: Launch Claude Code (2 minutes)

### 6.1 Start Claude Code

```bash
dsp
```

You should see the Claude Code interface:
```
╔══════════════════════════════════╗
║   Claude Code CLI Ready          ║
╚══════════════════════════════════╝
>
```

### 6.2 Test It

Type this prompt:
```
Hello! Can you verify my environment is set up correctly for the DocuMind workshop?
```

Claude should respond confirming it can access the workspace.

### 6.3 Exit Claude Code

When you're done:
```
exit
```
Or press **Ctrl+C**

---

## Final Checklist

Before starting the workshop, verify:

- [ ] Codespace is running (VS Code in browser)
- [ ] `.env` file exists with your API keys
- [ ] `npm install` completed successfully
- [ ] `npm test` passes all tests
- [ ] `dsp` command works
- [ ] You can navigate the file explorer
- [ ] You've looked at the README.md

**All checked?** You're ready for the Session 3 workshop!

---

## Quick Reference

### Commands You'll Use Often

```bash
# Launch Claude Code
dsp

# Exit Claude Code
exit

# Run tests
npm test

# View environment variables
echo $ANTHROPIC_API_KEY
```

### Keyboard Shortcuts in Codespaces

| Action | Shortcut |
|--------|----------|
| Open file quickly | Cmd/Ctrl + P |
| Open terminal | Ctrl + ` |
| Save file | Cmd/Ctrl + S |
| Search in files | Cmd/Ctrl + Shift + F |

### Getting Help

- **Stuck on setup?** Raise your hand during the workshop
- **Technical issues?** Check `docs/guides/TROUBLESHOOTING.md`
- **Questions about the course?** Ask in the course chat/Discord
- **Found a bug?** Create a GitHub Issue in your fork

---

## FAQ

**Q: Do I need to pay for API keys?**
A: Anthropic offers $5 free credit, which is plenty for the course. OpenAI charges pay-as-you-go, but embeddings cost about $0.01 total for all workshops.

**Q: Can I use my local machine instead of Codespaces?**
A: Yes, but Codespaces ensures everyone has the same environment. Ask your instructor for local setup instructions if needed.

**Q: How do I stop my Codespace when I'm done?**
A: Just close the browser tab. It auto-stops after 30 minutes of inactivity.

**Q: Can I come back to my work later?**
A: Yes! Your Codespace saves all your work. Go to [github.com/codespaces](https://github.com/codespaces) to reopen it.

**Q: What if I run out of API credits?**
A: The course exercises are designed to use minimal tokens. If you do run out, contact your instructor.

---

## Next Steps

**You're all set!**

1. Your instructor will provide the Session 3 Workshop file
2. Follow the exercises step-by-step
3. Ask questions if you get stuck
4. Have fun building DocuMind!

---

**Setup Issues?** Don't worry - we'll help you troubleshoot at the start of the workshop. Just let your instructor know.

**See you in Session 3!**

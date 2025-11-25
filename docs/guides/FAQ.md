# Frequently Asked Questions

## Setup & Environment

**Q: Do I need to pay for API keys?**
A: Anthropic offers $5 free credit, plenty for the course. OpenAI is pay-as-you-go but embeddings cost ~$0.01 total for all workshops.

**Q: Can I use my local machine instead of Codespaces?**
A: Yes, but Codespaces ensures consistent environments. Ask your instructor for local setup instructions.

**Q: How do I stop my Codespace?**
A: Close the browser tab. It auto-stops after 30 minutes of inactivity.

**Q: Can I come back to my work later?**
A: Yes! Go to github.com/codespaces to reopen your Codespace.

## Course Structure

**Q: How long does each session take?**
A: About 60-90 minutes including exercises.

**Q: Can I skip sessions?**
A: Not recommended. Each session builds on previous ones.

**Q: What if I fall behind?**
A: Review workshop files at your own pace. Solutions are discussed at the start of each session.

## Technical Questions

**Q: What's the difference between Skills and Subagents?**
A: Skills give Claude expertise (like hiring a consultant). Subagents are separate agents Claude delegates tasks to (like assigning work to a team member).

**Q: Why Supabase instead of MongoDB?**
A: Supabase offers PostgreSQL with pgvector for semantic search, plus generous free tier. Perfect for learning RAG systems.

**Q: Can I use a different AI model?**
A: Yes! Session 6 covers OpenRouter for multi-model access (GPT-4, Gemini, etc.).

## Common Problems

**Q: My API key isn't working**
A: Check: No quotes in .env, no spaces around =, key starts with correct prefix (sk-ant- for Anthropic).

**Q: Tests are failing**
A: Usually a .env issue. Run `source .env` and verify with `echo $ANTHROPIC_API_KEY`.

**Q: Codespace is slow**
A: Free tier has limited resources. Close unused tabs, restart if needed.

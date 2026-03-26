---
name: vault
description: Start a PKM session with the pkm-manager agent for your Obsidian vault. Use when you want to work with your vault — organizing notes, checking health, fixing metadata, finding duplicates, generating canvases, or just exploring what needs attention.
---

Invoke the pkm-manager agent to begin a vault session.

The agent should:
1. Confirm vault connection via `obsidian vault`
2. Run a quick health snapshot — orphan count, inbox size, any obvious schema drift
3. Ask what you'd like to focus on today, or surface the top 2-3 highest-priority issues if nothing is specified
4. Guide through the chosen workflow using vault-architect (new structures) or vault-curator (evolving existing content) as appropriate

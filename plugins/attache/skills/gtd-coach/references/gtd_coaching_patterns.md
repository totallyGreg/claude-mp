# GTD Coaching Patterns

Scenario-by-scenario coaching guidance, tool implementation notes, and response templates.

## Coaching by Scenario

### Inbox Processing

When a user has many unprocessed items:
1. Guide them through the clarify decision tree for each item
2. Help distinguish actionable from non-actionable
3. Apply the 2-minute rule
4. Help identify which items are actually projects

**Opening questions:**
- "How many items are in your inbox right now?"
- "When did you last process it to zero?"
- "Which ones have been sitting there longest?"

### Next Action Clarity

When tasks are vague:
1. Ask "What's the very next physical action?"
2. Help rewrite to be concrete and specific
3. Ensure the action starts with a verb
4. Test: "Can you picture yourself doing this?"

**Rewriting vague tasks:**

| Vague | Clarifying question | Concrete result |
|---|---|---|
| "Deal with contractor" | "What specifically needs to happen first?" | "Email contractor invoice #42 approval" |
| "Sort out finances" | "What's the single next step?" | "Download January bank statement" |
| "Think about hiring" | "What would move this forward?" | "Write job description for senior engineer" |

### Project Definition

When outcomes are unclear:
1. Ask "What does 'done' look like?"
2. Help write a clear outcome statement (starts with a verb, describes end state)
3. Identify the very next action
4. Set an appropriate review cadence

**Outcome statement formula:** `[Verb] [end state] by [optional constraint]`
- "Website redesign launched for Q2" ✓
- "Website stuff" ✗

### Weekly Review Coaching

Walk through in three parts:

**Get Clear (15–20 min)**
1. Process all inboxes to zero
2. Capture anything still in your head

**Get Current (20–30 min)**
3. Review each active project — does it have a next action?
4. Check Waiting For — follow up on stale items
5. Scan calendar (past week + next 2 weeks)

**Get Creative (10–15 min)**
6. Review Someday/Maybe — promote, keep, or drop
7. Brainstorm new ideas

### Stalled Project Recovery

When a project has no next action:
1. Ask: "What's the very next physical thing you could do?"
2. If stuck: "Is this still relevant? Or should it move to Someday/Maybe?"
3. If relevant: define the next action now before moving on

### System Overwhelm

When everything feels urgent:
1. Run `system-health` to get objective counts
2. Distinguish truly date-constrained items from noise
3. Review horizons — most "urgent" items are actually just visible
4. Pick one context, one energy level, work through the list

## Tool Implementation Guide

GTD works with any trusted system. The principles are the same; only the mechanics differ.

| Tool | Strengths | GTD fit |
|---|---|---|
| **OmniFocus** | Projects, contexts, perspectives, review mode, defer dates | Full GTD — best for power users |
| **Things 3** | Clean UI, areas, project headers | Simplified GTD — great for individuals |
| **Todoist** | Cross-platform, labels, filters | Works well with tags-as-contexts |
| **Notion/Obsidian** | Flexible structure | Requires discipline to maintain GTD shape |
| **Paper** | Zero friction capture | Classic GTD — David Allen's original system |
| **Plain text** | Markdown/org-mode | Highly portable, low overhead |

For OmniFocus-specific automation and queries, use the **omnifocus-core** skill.

## Response Templates

### After running system-health

```
Here's what your system shows:
- Inbox: X items (target: 0)
- Stalled projects: X (each needs a next action)
- Waiting For: X items (review for follow-up)

Let's start with [biggest pain point] — that's where you'll get the most relief.
```

### Diagnosing "I feel behind"

```
Let me ask a few diagnostic questions:
1. When did you last do a weekly review?
2. How many items are in your inbox?
3. Do your active projects all have next actions?

Usually "behind" means one of: inbox overflow, stalled projects, or missed review cadence.
```

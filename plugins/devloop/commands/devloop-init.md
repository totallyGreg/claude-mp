---
description: Set up the devloop in this git repository — loop.toml and the loop documents
argument-hint: [tier 0|1|2] [software|none]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/devloop/scripts/devloop.py:*), Bash(git status:*), Bash(git config:*), Bash(ls:*), Read, Glob, AskUserQuestion
---

Set up the development loop in this repository. Arguments, if given: $ARGUMENTS

1. Confirm this is a git repository where agents do the work (code, infrastructure,
   docs). Not for task lists or vault notes. Read any existing AGENTS.md, CLAUDE.md,
   BACKLOG or INBOX: init never overwrites a file, so note which will be kept.
2. Decide the inputs — from `$ARGUMENTS`, the repository itself (its build, test and
   check commands), and otherwise one AskUserQuestion call covering only what's missing:
   - **kind**: `software` when the repository has tests that can reproduce a bug;
     otherwise `none`.
   - **tier**: 0 (AGENTS + INBOX) for a small or short-lived repository; 1 (adds
     BACKLOG, PLAN, DECISIONS, LOOP and their checks) for multi-month work; 2 (adds
     the review gate and evals) only when the software profile has earned it.
   - **gate**: the one command "done" needs green.
   - **areas** (tier 1+): 4–12 nouns for what a change is *about*, read from the
     repository's own structure. They are never re-cut later, so propose, don't guess.
   - software: the test path prefixes and a test command that takes `{files}`.
3. Run `"${CLAUDE_PLUGIN_ROOT}"/skills/devloop/scripts/devloop.py init --gate "<gate>"
   --kind <kind> --tier <n> --areas "<A, B>" [--tests "<prefixes>" --test "<command>"]`.
4. Run `devloop.py check` and show its output, not a description of it.
5. Report what was written and kept, and the line to add to the gate. Do not commit
   and do not edit the build configuration; the user stages the files by name.

The skill `devloop` explains the loop, the tiers and `loop.toml` in full.

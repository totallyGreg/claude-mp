---
title: "feat: Add macOS Logging to terminal-guru skill"
type: feat
status: active
date: 2026-03-05
---

# feat: Add macOS Logging to terminal-guru skill

Add macOS unified logging coverage to the `terminal-emulation` skill, following the established pattern of a SKILL.md section + reference file.

## Problem Statement

The terminal-guru plugin covers terminal display and zsh development, but lacks coverage of macOS's unified logging system. The `log` command is a critical diagnostic tool for Apple admins and developers investigating system behavior, app crashes, and macOS-specific issues — a natural fit for the skill's diagnostic scope.

## Proposed Solution

1. Add a "macOS System Logging" section to `terminal-emulation` SKILL.md
2. Create `references/macos_logging_guide.md` following the pattern of `terminfo_guide.md` and `unicode_troubleshooting.md`
3. Update the diagnostic workflow table to include macOS logging as a symptom/domain entry

## Acceptance Criteria

- [ ] `references/macos_logging_guide.md` created covering: unified logging overview, `log show`, `log stream`, `log collect`, predicate filtering, log levels, subsystem/category filtering
- [ ] SKILL.md updated with a "macOS System Logging" section with common commands and when-to-use guidance
- [ ] Diagnostic workflow table updated with macOS logging row
- [ ] skillsmith evaluation run and score recorded

## Key Content (from reference source)

**Unified Logging system** (introduced WWDC 2016):
- Replaced flat-file `/var/log/` logs; still some flat files but unified log is canonical
- Console.app for GUI; `log` command for CLI flexibility

**Core `log` subcommands:**
```bash
# Show recent logs
sudo log show --last 1m
sudo log show --last 1h --start "2026-03-05 09:00:00"

# Real-time stream
sudo log stream

# Collect archive for later analysis
sudo log collect --output ~/Desktop/SystemLogs.logarchive --last 20m

# View archive
sudo log show --archive ~/Desktop/SystemLogs.logarchive
```

**Log levels:** default, info, debug, error, fault
```bash
sudo log show --last 1h --level debug
sudo log stream --level error
```

**Predicate filtering** (NSPredicate syntax):
```bash
# Filter by subsystem and category
sudo log stream --debug --predicate 'subsystem=="com.apple.sharing" and category=="AirDrop"'

# Filter by process name
sudo log stream --predicate 'processImagePath contains "Safari"'

# Filter by message content
sudo log show --last 1h --predicate 'eventMessage contains "error"'
```

**Common keys for predicates:**
- `subsystem` - reverse-DNS bundle ID namespace
- `category` - subsystem subcategory
- `processImagePath` - path to process binary
- `eventMessage` - the log message text
- `messageType` - log level (16=default, 17=info, 18=debug)

## Files to Change

### New: `plugins/terminal-guru/skills/terminal-emulation/references/macos_logging_guide.md`

Cover:
- What is unified logging (overview)
- `log show` — time filtering, archive viewing
- `log stream` — real-time monitoring
- `log collect` — capturing archives
- Log levels and `--level` flag
- Predicate filtering with NSPredicate syntax
- Common predicate keys and operators
- Practical examples (AirDrop, specific app, error scanning)
- Relationship to `/var/log/` flat files and Console.app

### Modified: `plugins/terminal-guru/skills/terminal-emulation/SKILL.md`

Add to "When to Use This Skill":
- Investigating macOS system behavior via unified logs

Add new section "4. macOS System Logging" with:
- Brief overview linking to reference
- Most-used commands (show, stream, collect, predicate)

Update diagnostic table in Step 2:
```
| macOS app/system issues, crashes | macOS Logging | references/macos_logging_guide.md |
```

## Sources

- Reference article: https://the-sequence.com/mac-logging-and-the-log-command-a-guide-for-apple-admins
- Existing pattern: `plugins/terminal-guru/skills/terminal-emulation/references/terminfo_guide.md`
- Existing SKILL.md: `plugins/terminal-guru/skills/terminal-emulation/SKILL.md`

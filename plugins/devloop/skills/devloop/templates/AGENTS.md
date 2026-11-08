# {{project}} — Agent Guide

**This file owns:** what every session needs: the index, the commands, and
each rule in one line with what enforces it. Only this file is loaded
automatically; the detail is in the documents below, read when the row
says. The devloop doc check caps its size and fails on a document it
doesn't list.

## Document Index

| Document | Owns | Read it when |
|----------|------|--------------|
{{index_rows}}

## Commands

```bash
{{gate}}    # the gate: "done" needs it green
{{commands}}
```

## Rules

Each names what enforces it, where something does.

{{rules}}

## The loop

{{loop_line}}

**Prefer mechanism over prose.** A rule in a sentence gets missed; a check
that fails cannot be.

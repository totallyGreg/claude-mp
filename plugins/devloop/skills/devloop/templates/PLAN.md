# {{project}} — Plan

**This file owns:** the queue of specified stages — work handed to an agent
or spanning sessions — in the order it should be built. A shipped stage
leaves this file; its `{{stages_dir}}/` file says `**Status:** shipped`.
**Do not put here:** progress (the stage file's `## Steps`), bugs and
small improvements ([{{backlog}}]({{backlog}})), decisions
([{{decisions}}]({{decisions}})).

## Remaining work

Ordered: the sequence encodes dependencies. The Why column says why the
stage exists, never how far it has got.

| P | Area | Stage | Title | Why |
|---|------|-------|-------|-----|

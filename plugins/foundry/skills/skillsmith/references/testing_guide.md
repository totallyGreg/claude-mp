# Skill Testing Methodology

Three testing areas defined by Anthropic's "Complete Guide to Building Skills for Claude," adapted for use with skillsmith's automated tooling.

---

## Area 1: Triggering Tests

**Goal:** Confirm the skill activates on relevant queries and does not activate on irrelevant ones.

**Target:** 90% trigger rate on the query set below.

### How to test

1. Construct a query set of 10 representative user messages that should invoke the skill. Draw these directly from your Use-Case Definition Form (see `references/form_templates.md`) and the trigger phrases in your `description` frontmatter.

2. Send each query to Claude without manually invoking the skill. Observe whether Claude routes to the skill automatically.

3. Construct 5 "should NOT trigger" queries — related topics that belong to a different skill or no skill.

4. Record results:

   | Query | Expected | Actual | Pass? |
   |-------|----------|--------|-------|
   | "review this PR" | Trigger | Trigger | ✅ |
   | "what is a pull request?" | No trigger | No trigger | ✅ |

**Pass criteria:** ≥9/10 relevant queries trigger the skill; 0/5 off-topic queries trigger it.

### Diagnosing failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Undertriggering (skill misses obvious invocations) | Too few trigger phrases, phrases too narrow | Add more specific quoted phrases to `description`; expand phrase variants |
| Overtriggering (skill fires on unrelated queries) | Phrases too generic, no negative triggers | Add `"Do NOT use for X (use Y instead)"` clause; narrow phrases with domain nouns |

Run `uv run scripts/evaluate_skill.py <path> --explain` to get automated coaching on description quality, including undertrigger and overtrigger signals.

---

## Area 2: Functional Tests

**Goal:** Confirm the skill produces valid outputs and makes zero failed tool calls on representative inputs.

**Target:** Valid output on all representative inputs; 0 failed API or tool calls.

### Automated subset

`--validate-functionality` covers the automated portion:

```bash
uv run scripts/evaluate_skill.py <skill-path> --validate-functionality
```

This verifies:
- SKILL.md parses and loads (required frontmatter present)
- Scripts exist, have shebangs, and are executable
- Reference files are readable
- No reference files exceed the large-file warning threshold without grep patterns

### Manual testing

The automated checks confirm structure only. For behavioral correctness, test these manually:

1. **Happy path:** Run the skill's primary use case end-to-end on a real input. Confirm the output matches the success criteria from your Use-Case Definition Form.

2. **Edge cases:** Test at least two edge cases — unusual inputs, missing data, or borderline triggers.

3. **Tool call errors:** Observe whether any tool calls fail during execution. Zero failed calls is the target.

4. **Reference loading:** Confirm Claude loads the right references when needed and does not load unnecessary ones.

**Post-validation checklist:**
- [ ] Happy path produces correct output
- [ ] Edge cases handled gracefully (not silently ignored)
- [ ] Zero failed tool calls in execution log
- [ ] References load on-demand, not all at startup

---

## Area 3: Performance Tests

**Goal:** Measure the skill's context budget impact and confirm it stays within acceptable bounds.

**Target:** Context overhead is predictable and documented.

### How to measure

1. **Baseline:** Run the target task without the skill. Record approximate message count and token usage.

2. **With skill:** Run the same task with the skill active. Record message count and token usage.

3. **Compute delta:**
   - Token overhead = (with skill tokens) − (baseline tokens)
   - Message overhead = (with skill messages) − (baseline messages)

4. **Document in plugin README.md** (optional but recommended for high-volume skills):
   ```
   Performance baseline: ~N additional tokens per invocation, ~M additional messages
   ```

### Automated signals

The evaluator gives static performance signals:

```bash
uv run scripts/evaluate_skill.py <skill-path>
```

| Metric | What it signals |
|--------|----------------|
| Conciseness score | Estimated token load from SKILL.md at activation |
| Progressive Disclosure score | Whether detailed content is deferred to references (loaded on-demand) |

A conciseness score below 60 usually indicates the skill loads too much content upfront. Move detailed content to `references/` and use progressive disclosure.

### Acceptance threshold

There is no universal token budget — it depends on the use case. A skill invoked dozens of times per session needs tighter bounds than one invoked once. Document your target in the plugin's README.md if performance is a concern.

---

## Running All Three Areas

Suggested order:

1. **Triggering** — fast to run; failing here means functional tests will be inconsistent
2. **Functional (automated)** — `--validate-functionality` takes seconds
3. **Functional (manual)** — required before first release
4. **Performance** — run when adding large reference files or after major rewrites

For pre-release validation:

```bash
# Automated quality + structure gate
uv run scripts/evaluate_skill.py <skill-path> --quick --strict

# Automated functionality gate
uv run scripts/evaluate_skill.py <skill-path> --validate-functionality

# Then manually run triggering and functional tests above
```

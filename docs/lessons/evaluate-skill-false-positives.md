# Evaluate Skill False Positives

**Date:** 2026-01-18
**Context:** Workflow documentation restructuring
**Related Skills:** skillsmith

## Issue

The `evaluate_skill.py` validation script reports false positive warnings about "deep nested references" when paths are mentioned in documentation examples.

## Example

When running evaluation on skillsmith:

```bash
uv run skills/skillsmith/scripts/evaluate_skill.py skills/skillsmith
```

**False Positive Warnings:**
```
⚠ Warnings:
  - Deep nested reference found (keep one-level deep):
    - **Examples**: `references/finance.md` for financial schemas,
      `references/mnda.md` for company NDA template
```

## Root Cause

The `validate_file_references()` function in `evaluate_skill.py` (line 821-848) checks for path patterns in the SKILL.md body:

```python
def validate_file_references(skill_path, body):
    """Validate file references use relative paths"""
    issues = []

    # Check for deeply nested references
    if 'references/' in body:
        lines = body.split('\n')
        for line in lines:
            if 'references/' in line:
                # Count directory depth
                if line.count('/') > 2:  # references/subdir/file = 2 levels
                    issues.append(f"Deep nested reference found: {line.strip()}")
```

**Problem:** This logic doesn't distinguish between:
1. **Actual file references:** `Load references/api_reference.md for details`
2. **Example paths in documentation:** "You might create `references/finance.md` for schemas"
3. **Code examples:** `` `references/example.md` ``

The function counts all occurrences, including those in:
- Inline code spans (`` `path` ``)
- Code blocks (```...```)
- Documentation examples
- Lists of example files

## Impact

**Low severity:**
- Warnings don't fail validation (skill still passes)
- Doesn't affect skill functionality
- Just creates noise in validation output

**Confusion:**
- Developers may spend time investigating non-issues
- Makes it harder to spot real problems in validation output

## Potential Solutions

### Option 1: Improve Context Awareness

Enhance `validate_file_references()` to skip:
- Content within code blocks (```...```)
- Content within inline code spans (`` `...` ``)
- Lines that are clearly examples (contain "example", "e.g.", "such as")

```python
def validate_file_references(skill_path, body):
    """Validate file references use relative paths"""
    issues = []

    # Parse body, skipping code blocks
    in_code_block = False
    lines = body.split('\n')

    for line in lines:
        # Skip code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Skip inline code examples
        if 'references/' in line:
            # Remove inline code spans
            import re
            cleaned_line = re.sub(r'`[^`]+`', '', line)

            # Check if references/ still present after removing code spans
            if 'references/' in cleaned_line:
                if cleaned_line.count('/') > 2:
                    issues.append(f"Deep nested reference found: {line.strip()}")
```

### Option 2: Make Warning More Specific

Update the warning message to acknowledge potential false positives:

```python
issues.append(f"Possible deep nested reference: {line.strip()} "
              "(Note: May be false positive if this is a documentation example)")
```

### Option 3: Document and Accept

Accept that validation has false positives for documentation-heavy skills and document this behavior:
- Add comment in `evaluate_skill.py` explaining the limitation
- Document in this lessons learned file
- Consider it acceptable tradeoff for simple validation logic

## Current Recommendation

**Option 3** (Document and Accept) is most pragmatic:

**Pros:**
- No risk of breaking existing validation
- Simple to maintain
- False positives are low-severity warnings

**Cons:**
- Noise in validation output
- Requires developers to understand the quirk

**Future Improvement:**
If false positives become problematic, implement Option 1 to improve context awareness.

## Workarounds

### For Skill Authors

When writing SKILL.md documentation:

**Instead of:**
```markdown
Examples: `references/finance.md`, `references/policies.md`
```

**Use:**
```markdown
Examples: `finance.md` and `policies.md` in references/
```

This avoids triggering the path depth check while remaining clear.

### For Validation

When reviewing evaluation output:
1. Check if warnings mention obvious documentation/examples
2. Verify if actual file structure has deep nesting
3. If mismatch, ignore the warning

Run this to see actual file structure:
```bash
find skills/skillsmith/references -type f
```

## Related

- `skills/skillsmith/scripts/evaluate_skill.py` - Validation logic
- Function: `validate_file_references()` (line 821-848)
- Function: `validate_agentskills_spec()` (line 851-896)

## Key Takeaways

1. **Validation has false positives** for path mentions in documentation
2. **Low impact** - warnings only, doesn't fail validation
3. **Known limitation** - simple string matching can't understand context
4. **Acceptable tradeoff** - keeps validation logic simple
5. **Future improvement** - could add context awareness if needed

## Action Items

- [x] Document this quirk in lessons learned
- [ ] Consider adding comment in `evaluate_skill.py` about false positives
- [ ] Monitor if false positives become problematic enough to warrant fixing

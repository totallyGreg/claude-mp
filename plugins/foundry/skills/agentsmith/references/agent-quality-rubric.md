# Agent Quality Rubric

Scoring rubric for `evaluate_agent.py`. Three dimensions, weighted to 100.

## Dimension 1: Trigger Effectiveness (weight: 0.35)

Measures how well the description's `<example>` blocks trigger the agent.

| Sub-metric | Max | Scoring |
|---|---|---|
| **Example count** | 25 | 0 examples = 0, 1 = 10, 2 = 15, 3 = 20, 4+ = 25 |
| **Example variety** | 25 | Types: explicit ("user asks to X"), proactive ("after user does X"), implicit/edge-case. 3 types = 25, 2 = 18, 1 = 10 |
| **Commentary presence** | 15 | `(examples with <commentary>) / total * 15` |
| **Negative triggers** | 15 | Description says when NOT to use the agent. Present = 15, absent = 0 |
| **Phrasing variety** | 10 | User messages across examples use different wording. High Jaccard distance = 10, moderate = 7, low = 3 |
| **Description specificity** | 10 | Not too generic ("helps the user") or too narrow. Specific + examples = 10, some specificity = 6, generic = 2 |

## Dimension 2: System Prompt Quality (weight: 0.35)

Measures the quality of the markdown body after the frontmatter closing `---`.

| Sub-metric | Max | Scoring |
|---|---|---|
| **Role specificity** | 15 | First paragraph defines a specific role with domain language. Specific + 2 domain words = 15, partial = 10, minimal = 6 |
| **Concrete responsibilities** | 15 | Numbered/bulleted responsibility items. 10+ = 15, 5+ = 12, 2+ = 8, <2 = 3 |
| **Step-by-step process** | 15 | Documented workflow with clear steps. Strong indicators = 15, moderate = 10, weak = 5 |
| **Quality standards** | 10 | MUST/ALWAYS/NEVER/CRITICAL constraints. 4+ hits = 10, 2+ = 7, 1 = 4 |
| **Output format** | 10 | Defines expected output structure. 2+ indicators = 10, 1 = 6 |
| **Edge case handling** | 10 | Documents error cases and fallbacks. 3+ = 10, 2 = 7, 1 = 4 |
| **Length sweet spot** | 15 | Word count: <200 = 0, 200-500 = 8, **500-3000 = 15**, 3000-10000 = 10, 10000+ = 5 |
| **Structural organization** | 10 | Markdown headings for sections. 5+ = 10, 3+ = 7, 1+ = 4 |

## Dimension 3: Coherence (weight: 0.30)

Measures consistency between description, body, and tools.

| Sub-metric | Max | Scoring |
|---|---|---|
| **Example-body alignment** | 30 | Action verbs from examples should appear in body. >=70% overlap = 30, >=50% = 22, >=30% = 15 |
| **Body-example coverage** | 25 | Body sections should have examples that exercise them. >=60% covered = 25, >=30% = 18, some = 10 |
| **Tool scope fitness** | 25 | Declared tools referenced in body; no undeclared tools used. Good fit = 25, partial = 18, weak = 10 |
| **Terminology consistency** | 20 | Key terms in description also appear in body. >=60% overlap = 20, >=40% = 14, >=20% = 8 |

## Baseline Regression Detection

- Baselines stored in `.agentsmith-baselines.json` in the agent's plugin root
- Created automatically on first evaluation run
- Subsequent runs report delta: `+N` or `-N (REGRESSION)`

## Agent File Detection

| Pattern | Location | Identifier |
|---|---|---|
| **Flat** | `agents/name.md` | Single markdown file with YAML frontmatter |
| **Directory** | `agents/name/AGENT.md` | AGENT.md inside a subdirectory |

Both patterns share the same YAML frontmatter format with `name`, `description`, `model`, `color`, `tools` fields.

## Context-Aware Evaluation

- YAML frontmatter is parsed separately from body content
- Code blocks (``` ... ```) are stripped before body heuristic analysis to prevent false positives
- Example blocks in the description are parsed structurally, not via regex on the raw description

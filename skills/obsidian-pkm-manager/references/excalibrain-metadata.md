# Excalibrain Metadata Guide

Excalibrain is an Obsidian plugin that creates visual graph representations of notes based on semantic relationships defined in frontmatter. This guide covers the metadata structure Excalibrain uses.

## Overview

Excalibrain visualizes notes as nodes in a graph with different types of connections representing different relationships. The plugin uses specific frontmatter fields to determine how notes connect to each other.

**Key Concept:** Unlike simple backlinks, Excalibrain provides *semantic* meaning to relationships:
- **Parent** - Broader concept or category
- **Child** - Narrower concept or instance
- **Left Friend** - Related concept (same category)
- **Right Friend** - Related concept (different context)

## Core Relationship Fields

### Parent Relationship

Indicates a broader concept, category, or container.

```yaml
---
parent: [[Broader Concept]]
---
```

**Examples:**
```yaml
# Note: JavaScript
parent: [[Programming Languages]]

# Note: Sprint Planning
parent: [[Agile Methodology]]

# Note: Customer Meeting Notes
parent: [[Acme Corp]]
```

**Multiple Parents:**
```yaml
parent:
  - [[Category A]]
  - [[Category B]]
```

### Child Relationship

Indicates narrower concepts, instances, or components.

```yaml
---
child:
  - [[Specific Instance 1]]
  - [[Specific Instance 2]]
---
```

**Examples:**
```yaml
# Note: Programming Languages
child:
  - [[JavaScript]]
  - [[Python]]
  - [[Rust]]

# Note: Project Alpha
child:
  - [[Feature Implementation]]
  - [[Testing Strategy]]
  - [[Deployment Plan]]
```

### Left Friend Relationship

Related concepts within the same category or domain.

```yaml
---
left-friend:
  - [[Related Concept 1]]
  - [[Related Concept 2]]
---
```

**Examples:**
```yaml
# Note: JavaScript
left-friend:
  - [[TypeScript]]
  - [[Python]]
  - [[Ruby]]

# Note: Agile Methodology
left-friend:
  - [[Scrum]]
  - [[Kanban]]
  - [[XP]]
```

**Usage Pattern:** "Things like this" or "alternatives to this"

### Right Friend Relationship

Related concepts from different categories or contexts.

```yaml
---
right-friend:
  - [[Different Context 1]]
  - [[Different Context 2]]
---
```

**Examples:**
```yaml
# Note: JavaScript
right-friend:
  - [[Node.js Runtime]]
  - [[React Framework]]
  - [[VS Code Editor]]

# Note: Customer Success
right-friend:
  - [[Sales Process]]
  - [[Product Development]]
  - [[Support Engineering]]
```

**Usage Pattern:** "Related but different type" or "commonly used with"

## Default Field Names (Configurable)

Excalibrain's default field names are:

```yaml
parent: [[Parent Note]]
children:
  - [[Child Note]]
left-friends:
  - [[Related Note]]
right-friends:
  - [[Associated Note]]
```

**Note:** These field names are configurable in Excalibrain settings. Check your vault's Excalibrain configuration to see what fields are actually being used.

## Common Field Name Variations

Based on the Excalibrain codebase, these are typical variations:

```yaml
# Parent variations
parent: [[Note]]
parents: [[Note]]
up: [[Note]]

# Child variations
child: [[Note]]
children: [[Note]]
down: [[Note]]

# Friend variations
left-friend: [[Note]]
left-friends: [[Note]]
friend: [[Note]]
friends: [[Note]]

# Right friend variations
right-friend: [[Note]]
right-friends: [[Note]]
```

## Complete Example

```yaml
---
title: JavaScript
aliases: [JS, ECMAScript]
parent: [[Programming Languages]]
child:
  - [[ES6 Features]]
  - [[Async Patterns]]
  - [[DOM Manipulation]]
left-friend:
  - [[TypeScript]]
  - [[Python]]
  - [[Ruby]]
right-friend:
  - [[Node.js]]
  - [[React]]
  - [[VS Code]]
tags: [programming, web-dev]
---
```

## Visualization in Excalibrain

The graph displays relationships spatially:

```
                    [Programming Languages]
                             ↑
                          parent
                             |
    [TypeScript] ← left-friend → [JavaScript] → right-friend → [Node.js]
                                      |
                                   child
                                      ↓
                              [ES6 Features]
```

## Relationship Design Patterns

### Pattern 1: Hierarchical Organization

For taxonomy or categorical structures:

```yaml
# Top Level: Computing
child:
  - [[Programming]]
  - [[Networking]]
  - [[Security]]

# Mid Level: Programming
parent: [[Computing]]
child:
  - [[Programming Languages]]
  - [[Development Tools]]
  - [[Design Patterns]]

# Bottom Level: Programming Languages
parent: [[Programming]]
child:
  - [[JavaScript]]
  - [[Python]]
  - [[Rust]]
```

### Pattern 2: Project Structure

For project and task relationships:

```yaml
# Project Note
title: Website Redesign
child:
  - [[Design Phase]]
  - [[Development Phase]]
  - [[Testing Phase]]
right-friend:
  - [[Marketing Campaign]]
  - [[Content Strategy]]

# Task Note
title: Design Phase
parent: [[Website Redesign]]
child:
  - [[Wireframes]]
  - [[Visual Design]]
  - [[User Testing]]
```

### Pattern 3: Knowledge Domain Mapping

For interconnected concepts:

```yaml
# Concept Note
title: Machine Learning
parent: [[Artificial Intelligence]]
child:
  - [[Supervised Learning]]
  - [[Unsupervised Learning]]
  - [[Reinforcement Learning]]
left-friend:
  - [[Deep Learning]]
  - [[Neural Networks]]
  - [[Data Science]]
right-friend:
  - [[Python]]
  - [[TensorFlow]]
  - [[Statistics]]
```

### Pattern 4: Company/Customer Organization

```yaml
# Company Note
title: Acme Corp
child:
  - [[Q4 2025 Engagement]]
  - [[Product Integration]]
  - [[Support Tickets]]
right-friend:
  - [[John Doe]]
  - [[Jane Smith]]

# Engagement Note
title: Q4 2025 Engagement
parent: [[Acme Corp]]
child:
  - [[2025-12-01 Kickoff Meeting]]
  - [[2025-12-08 Status Update]]
right-friend:
  - [[Project Alpha]]
  - [[Migration Plan]]

# Meeting Note
title: 2025-12-01 Kickoff Meeting
parent: [[Q4 2025 Engagement]]
right-friend:
  - [[John Doe]]
  - [[Action Items]]
```

## Integration with Bases

Excalibrain metadata and Bases queries work together:

**Excalibrain:** Visual exploration of relationships
**Bases:** Tabular display of related notes

```yaml
---
title: Customer Project
parent: [[Acme Corp]]
child:
  - [[Meeting 1]]
  - [[Meeting 2]]
tags: [project, customer]
---

# Visual Exploration
Excalibrain graph shows parent/child structure

# Tabular Details
![[Meetings.base#Project Meetings]]
```

Bases query can filter on parent/child:

```yaml
# In Meetings.base
views:
  - type: table
    name: Project Meetings
    filters:
      parent == [this.file.link]
```

## Migration from Dataview Inline Fields

**Old Dataview Pattern:**
```markdown
Parent:: [[Note]]
Child:: [[Note1]], [[Note2]]
```

**New Excalibrain Pattern:**
```yaml
---
parent: [[Note]]
child:
  - [[Note1]]
  - [[Note2]]
---
```

**Why:** Bases doesn't support inline fields, so all metadata must be in frontmatter.

## Best Practices

### 1. Be Intentional with Relationships

Not every link needs to be a semantic relationship:

- **Use parent/child** for clear hierarchies
- **Use friends** for meaningful associations
- **Use regular links** for casual references

### 2. Maintain Reciprocal Relationships

If Note A has `child: [[Note B]]`, then Note B should have `parent: [[Note A]]`.

**Consider automating this** with templates:

```markdown
<%*
// When creating a child note, prompt for parent
const parentNote = await tp.system.prompt("Parent note:");
-%>
---
parent: [[<% parentNote %>]]
---
```

### 3. Don't Over-Structure

Not every note needs semantic relationships. Use them where they add value for exploration and understanding.

### 4. Combine with Tags

```yaml
---
parent: [[Projects]]
tags: [active, high-priority]
---
```

Tags for categorical filtering, parent/child for structural relationships.

### 5. Document Your Schema

Create a note explaining your relationship conventions:

```markdown
# Relationship Conventions

## Parent/Child
- Use for: Taxonomies, project structures, categorical hierarchies
- Parent = broader concept
- Child = narrower instance

## Left Friends
- Use for: Alternatives, similar concepts in same domain
- Example: Programming languages, methodologies

## Right Friends
- Use for: Related but different types, commonly used together
- Example: Language → Framework, Concept → Tool
```

## Common Pitfalls

### 1. Circular References

Avoid:
```yaml
# Note A
parent: [[Note B]]

# Note B
parent: [[Note A]]
```

### 2. Too Many Relationships

Doesn't help:
```yaml
child:
  - [[Note 1]]
  - [[Note 2]]
  # ... 30 more notes
```

**Better:** Use intermediate categorization nodes.

### 3. Inconsistent Direction

Mixing:
```yaml
# Some notes use parent
parent: [[Category]]

# Others use child from category
# (in Category note)
child: [[This Note]]
```

**Better:** Pick one pattern and stick with it.

### 4. Relationship Mismatch

Wrong:
```yaml
# JavaScript note
parent: [[React]]  # React is not broader than JavaScript
```

Correct:
```yaml
# JavaScript note
child: [[React]]  # React is a JavaScript framework
# OR
right-friend: [[React]]  # If you want to show association
```

## Checking Excalibrain Settings

To verify which fields your Excalibrain uses:

1. Open Obsidian Settings
2. Go to Excalibrain plugin settings
3. Look for "Relationship Field Names" or similar
4. Note the exact field names configured

Common settings locations:
- Parent field: `parent`, `parents`, `up`
- Child field: `child`, `children`, `down`
- Friend fields: `friend`, `friends`, `left-friend`, `right-friend`

Adjust templates to match your configuration.

## Template Integration

**Example: New Concept Note Template**

```markdown
<%*
const conceptName = await tp.system.prompt("Concept name:");
const parentConcept = await tp.system.prompt("Parent concept (optional):", "", false, false);
const similarConcepts = await tp.system.prompt("Similar concepts (comma-separated):", "", false, false);

await tp.file.rename(conceptName);
await tp.file.move("Concepts/" + conceptName);
-%>
---
title: <% conceptName %>
<% if (parentConcept) { %>parent: [[<% parentConcept %>]]<% } %>
<% if (similarConcepts) { %>
left-friend:
<%* similarConcepts.split(",").forEach(concept => { -%>
  - [[<% concept.trim() %>]]
<%* }); -%>
<% } %>
tags: [concept]
---
# <% conceptName %>

<% tp.file.cursor(1) %>

## Related Concepts
![[Concepts.base#Related]]
```

This creates a note with Excalibrain relationships while also embedding a Bases view for tabular context.

## Resources

- [Excalibrain GitHub Repository](https://github.com/zsviczian/excalibrain)
- [Excalibrain Settings Reference](https://github.com/zsviczian/excalibrain/blob/master/src/lang/locale/en.ts) - Lines 19-24 define default field names
- Obsidian Forum: Search for "Excalibrain" for community examples and discussions

---

**Remember:** Excalibrain is for *visual exploration*, Bases is for *querying and tabular display*. Use both together for a complete PKM experience.

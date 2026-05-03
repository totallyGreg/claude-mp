# Canvas Types

The vault uses four canvas types. Recommend and generate the correct type based on what the user is trying to understand.

**Impact Map** — "If I change X, what else breaks or needs updating?"
- Nodes: vault resources (notes, templates, bases, canvases, external systems)
- Edges: `embeds`, `sources from`, `scoped by`, `drives`, `created from`, `listed in`, `documents`
- Recommend when: user changes a template, schema, base, or moves files

**Workflow Map** — "How does this process work, and what composes it?"
- Nodes: triggers, steps, tools, outputs, sub-workflows
- Edges: `triggers`, `executes`, `produces`, `composed of`, `requires`
- Recommend when: user is documenting a process or asking "how does X work"

**Architecture Map** — "How is this domain structured?"
- Nodes: folders, collections, note types, relationships
- Edges: `contains`, `inherits from`, `scoped to`, `indexes`
- Recommend when: user wants an overview of a domain's structure

**Knowledge Map** — "What connects to what by topic?"
- Nodes: notes and their wikilinks
- Edges: `links to`, `referenced by`
- Recommend when: user wants to explore a topic cluster; auto-generate via `/canvas`

**Novel uses:** Canvas types can be layered. When a canvas serves two purposes, name it by primary purpose and note the secondary in a text node.

**See also:** `700 Notes/Notes/Canvas Types.md` in the vault for the full reference.

# Folder Structure Examples

This document provides example folder structures for different Personal Knowledge Management approaches in Obsidian.

## Guiding Principles

1. **Folders are for broad categorization** - Use metadata and queries for detailed organization
2. **Archivable units** - Structure should support moving/archiving whole sections
3. **Scannable at a glance** - Top level should be easy to navigate visually
4. **Supports your workflow** - Structure should match how you think and work

## Structure 1: Johnny Decimal Inspired

Based on decimal categorization with numbered prefixes:

```
Vault/
├── 000-099 System/
│   ├── 000 Index/
│   ├── 010 Templates/
│   └── 020 Scripts/
├── 100-199 Personal/
│   ├── 100 Journal/
│   │   ├── Daily/
│   │   ├── Weekly/
│   │   └── Monthly/
│   ├── 110 Health/
│   ├── 120 Finance/
│   └── 130 Goals/
├── 200-299 Knowledge/
│   ├── 200 Concepts/
│   ├── 210 References/
│   ├── 220 Terminology/
│   └── 230 Learning/
├── 300-399 Work/
│   ├── 300 Projects/
│   ├── 310 Meetings/
│   ├── 320 Customers/
│   └── 330 People/
├── 400-499 Creative/
│   ├── 400 Writing/
│   ├── 410 Ideas/
│   └── 420 Art/
└── 900-999 Archive/
    ├── 900 Completed Projects/
    └── 910 Old Jobs/
```

**Pros:**
- Clear categorization
- Easy to extend
- Numerical ordering keeps structure consistent

**Cons:**
- Can feel rigid
- Requires planning category numbers
- May need renumbering when adding top-level categories

## Structure 2: PARA Method

Projects, Areas, Resources, Archives:

```
Vault/
├── 0 System/
│   └── Templates/
├── 1 Projects/
│   ├── Active/
│   │   ├── Website Redesign/
│   │   ├── Book Writing/
│   │   └── Home Renovation/
│   └── Planning/
├── 2 Areas/
│   ├── Health/
│   ├── Career/
│   ├── Finance/
│   ├── Relationships/
│   └── Learning/
├── 3 Resources/
│   ├── Articles/
│   ├── Books/
│   ├── Courses/
│   ├── People/
│   └── Companies/
└── 4 Archive/
    ├── Completed Projects/
    └── Old Areas/
```

**Pros:**
- Clear separation of active vs reference
- Projects have defined start/end
- Easy to archive completed work

**Cons:**
- Distinction between Areas and Resources can be fuzzy
- Frequent movement of notes between sections

## Structure 3: Zettelkasten Inspired

Minimal folders, maximum linking:

```
Vault/
├── System/
│   ├── Templates/
│   └── Index/
├── Fleeting/
│   └── [Daily inbox notes]
├── Literature/
│   └── [Source material notes]
├── Permanent/
│   └── [Developed ideas]
└── Projects/
    └── [Active project notes]
```

**Pros:**
- Simple structure
- Encourages linking over filing
- Focused on idea development

**Cons:**
- Can become overwhelming without good metadata
- Requires discipline to process fleeting notes
- Not suitable for work/project management

## Structure 4: Temporal + Categorical Hybrid

User's current structure (from conversation):

```
Vault/
├── 500 ♽ Cycles/
│   ├── 510 🌏 Years/
│   ├── 520 🌄 Days/
│   ├── 530 🗓 Weeks/
│   ├── 540 📅 Months/
│   └── 550 ⌛️ Quarters/
├── 700 Notes/
│   ├── Companies/
│   ├── Ideas💡/
│   ├── Meetings/
│   ├── Omnivore/
│   ├── PAN Notes/
│   │   └── Customers/
│   ├── People/
│   └── Terminology/
├── 900 📐Templates/
│   ├── 910 File Templates/
│   ├── 920 File Classes/
│   ├── 930 Field Templates/
│   ├── 970 Bases/
│   ├── 980 AI Prompts/
│   └── Scripts/
└── Skills/
```

**Pros:**
- Clear separation of temporal and categorical
- Temporal hierarchy supports review workflow
- Work notes grouped for archiving

**Cons:**
- Can accumulate notes in generic "Notes" folder
- Emoji prefixes not universally supported
- May need refinement over time

**Refinement Opportunities:**
- Clarify purpose of top-level "700 Notes"
- Consider separating personal from work more clearly
- Evaluate if decimal numbering serves current workflow

## Structure 5: Context-Based

Organized by context of use:

```
Vault/
├── System/
│   ├── Templates/
│   ├── Bases/
│   └── Scripts/
├── Work/
│   ├── CurrentJob/
│   │   ├── Customers/
│   │   ├── Projects/
│   │   ├── Meetings/
│   │   └── People/
│   ├── Career/
│   └── Archive/
│       └── 2020-2023 PreviousJob/
├── Personal/
│   ├── Journal/
│   ├── Health/
│   ├── Finance/
│   └── Relationships/
├── Learning/
│   ├── Concepts/
│   ├── Terminology/
│   ├── Courses/
│   └── Books/
└── Creative/
    ├── Ideas/
    ├── Writing/
    └── Projects/
```

**Pros:**
- Clear context switching
- Easy to separate work from personal
- Supports different access patterns

**Cons:**
- Some notes may fit multiple contexts
- Projects may span contexts

## Structure 6: MOC (Map of Content) Driven

Minimal folders, heavy MOC usage:

```
Vault/
├── System/
├── MOCs/
│   ├── Programming MOC/
│   ├── Health MOC/
│   ├── Projects MOC/
│   └── People MOC/
├── Daily/
├── Notes/
└── Archive/
```

Each MOC aggregates notes via Bases queries.

**Pros:**
- Maximum flexibility
- Structure emerges from content
- Easy to create overlapping organizations

**Cons:**
- Requires active MOC maintenance
- Can be hard to find things without good search
- Needs strong metadata discipline

## Choosing a Structure

### Questions to Ask:

1. **How do you naturally think about information?**
   - Temporally (when)
   - Categorically (what)
   - Contextually (where/why)
   - Relationally (connected how)

2. **What's your primary use case?**
   - Work project management → Context or PARA
   - Knowledge building → Zettelkasten or MOC
   - Life management → PARA or Hybrid
   - Research → Zettelkasten
   - Mixed → Hybrid

3. **How do you want to archive?**
   - By time period → Temporal
   - By project → PARA or Context
   - Rarely → Zettelkasten/MOC

4. **How do you find information?**
   - Browsing folders → Clear categorical
   - Search → Minimal folders, good metadata
   - Graphs → MOC or Zettelkasten
   - Queries → Any structure with metadata

### Evolution Over Time

**Most vaults evolve through stages:**

1. **Initial:** Simple, few folders
2. **Growth:** Add categories as needs emerge
3. **Refinement:** Consolidate, clarify purpose
4. **Optimization:** Metadata-driven, minimal folders

Don't over-engineer early. Let structure emerge from use.

## Recommended: Job-Agnostic Work Structure

For work notes that survive job changes:

```
Vault/
├── Companies/
│   └── [Company profiles - persist across jobs]
├── Work/
│   ├── CurrentEmployer/
│   │   ├── Customers/
│   │   ├── Projects/
│   │   ├── Meetings/
│   │   └── Internal/
│   └── Archive/
│       ├── 2018-2020 CompanyA/
│       └── 2020-2023 CompanyB/
└── Career/
    ├── Skills/
    ├── Certifications/
    └── Resume/
```

**Key principles:**
1. Company profiles separate from job-specific notes
2. Current job in clearly named folder
3. Archive folders include date ranges
4. Career notes persist across all jobs

**Template adjustment when changing jobs:**

Search and replace in templates:
- `"Work/CurrentEmployer/"` → `"Work/NewCompany/"`

Or use dynamic selection:

```javascript
<%*
const employer = await tp.system.suggester(
  (item) => item,
  ["CurrentEmployer", "Archive/2020-2023 CompanyB"]
);
const folder = "Work/" + employer + "/Meetings/";
await tp.file.move(folder + filename);
-%>
```

## Folder Naming Conventions

### Prefixes

**Numbers:**
- `000-099` for system/meta
- `100-199` for first major category
- Increments of 10 within categories

**Emojis:**
- Clear visual distinction
- May have compatibility issues
- Consider accessibility

**None:**
- Clean, professional
- Relies on alphabetical ordering
- May need manual ordering

### Capitalization

**Title Case:** `My Important Notes`
- Professional appearance
- Easier to read

**lowercase:** `my important notes`
- Faster to type
- Consistent with many file systems

**UPPERCASE:** `MY IMPORTANT NOTES`
- High visibility
- Can feel like shouting

**Pick one and be consistent.**

## Anti-Patterns to Avoid

### 1. Over-Nesting

**Bad:**
```
Projects/
└── Active/
    └── Work/
        └── Customer/
            └── ProjectX/
                └── Phase1/
                    └── Tasks/
```

**Better:**
```
Projects/
└── ProjectX-Customer/
```

Use metadata for hierarchical organization:
```yaml
customer: [[Customer]]
phase: Phase1
status: active
```

### 2. Duplicate Categorization

**Bad:**
```
Notes/Work/Meetings/
Notes/Meetings/Work/
```

Pick one organization scheme.

### 3. Premature Optimization

Don't create 50 folders before you have 50 notes. Let structure emerge.

### 4. Mixing Concerns

**Bad:**
```
Projects/
├── Website Redesign/
├── Meeting with Client/
├── Template/
└── Ideas for Future/
```

**Better:** Separate projects, meetings, templates, ideas into different areas.

## Migration Strategy

When restructuring:

1. **Document current state** - Take note of existing structure
2. **Design new structure** - Plan before moving
3. **Update templates first** - Ensure new notes go to right place
4. **Migrate incrementally** - Don't try to move everything at once
5. **Update Bases queries** - Adjust folder filters
6. **Test thoroughly** - Verify links and embeds still work
7. **Document in System Guide** - Record the change and rationale

## Folder Structure Checklist

When evaluating or designing structure:

- [ ] Top level is scannable (< 10 folders)
- [ ] Each folder has a clear, single purpose
- [ ] Nesting depth is minimal (< 4 levels)
- [ ] Naming is consistent (case, prefixes, separators)
- [ ] Work and personal are appropriately separated
- [ ] Archive path is clear
- [ ] Templates reference correct paths
- [ ] Bases queries use correct folder filters
- [ ] Structure supports how you actually work
- [ ] Can explain structure to someone else simply

## Example: User's Potential Refinement

Current (simplified):
```
500 Cycles/ (temporal)
700 Notes/ (catch-all)
900 Templates/
```

Potential evolution:
```
500 ♽ Temporal/
    ├── Daily/
    ├── Weekly/
    ├── Monthly/
    ├── Quarterly/
    └── Yearly/
700 💼 Work/
    ├── Companies/
    ├── CurrentEmployer/
    └── Archive/
750 🧠 Knowledge/
    ├── Ideas/
    ├── Concepts/
    ├── Terminology/
    └── References/
800 👤 People/
900 📐 System/
    ├── Templates/
    ├── Bases/
    └── Scripts/
```

Changes:
- Flattened temporal hierarchy
- Separated work from knowledge
- Created dedicated People folder
- Clarified purpose of each section

**Before making changes:** Test with a few notes, verify templates and queries work, document the change.

---

Remember: The best structure is the one you'll actually use. Start simple, evolve based on real needs, not theoretical perfection.

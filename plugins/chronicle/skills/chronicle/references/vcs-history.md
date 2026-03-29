# VCS History and Non-Code Use Cases

Understanding where version control came from clarifies why modern tools make the choices they do. Each generation of VCS solved the failures of its predecessor.

## The Lineage

### RCS — Revision Control System (1982)

The first widely used version control system. RCS tracked individual files using reverse delta storage: the current version is stored in full, and older versions are reconstructed by applying patches backward.

**Model**: file-level locking. To edit a file, check it out (locking it), make changes, check it back in. Only one person can edit a file at a time.

**Limitations**:
- No concept of a project or changeset — each file is tracked independently
- Locking model is serializing and pessimistic
- No networking; files must be on a shared filesystem

**Legacy**: RCS is still shipped with many Unix systems. `ci`/`co` commands and the `.v` file format remain recognizable. The reverse delta approach influenced all subsequent VCS storage designs.

**Concepts that survived**: the commit (checkin), revision numbers, the log.

---

### CVS — Concurrent Versions System (1990)

CVS eliminated RCS's file-level locking and introduced optimistic concurrency: multiple developers edit the same files simultaneously, and conflicts are resolved at commit time rather than prevented by locking.

**Model**: centralized server, directory-level tracking, optimistic merge.

**Innovations over RCS**:
- Concurrent editing without locking
- Directory-level (not file-level) version tracking
- Branching and tagging across the whole project
- Network access to the repository

**Limitations**:
- No atomic commits: a multi-file commit could partially succeed
- Renames and moves were not tracked (a rename was a delete + add)
- Branches were expensive and rarely used
- Binary files handled poorly

**Legacy**: CVS's model of optimistic concurrency is the basis for all modern distributed VCS. The concept of a "repository" and "working copy" originates here.

---

### Subversion — SVN (2000)

Built explicitly to fix CVS's limitations while retaining its centralized model.

**Model**: centralized server, atomic commits, full directory tracking.

**Improvements over CVS**:
- Atomic commits: all files in a commit succeed or all fail
- Directory versioning: renames, moves, and copies are tracked
- Better binary file handling
- Consistent revision numbers (global integer, not per-file)
- Properties on files and directories

**Limitations**:
- Centralized: all operations require server access; offline work is limited
- Branching is cheap syntactically (it's just a copy) but expensive operationally (merging back is manual and error-prone)
- Merge tracking improved over time but never became natural

**Still relevant**: SVN remains in production in large enterprises, regulated industries (finance, aerospace, government), and organizations that built tooling around it. Many CI/CD systems support SVN. For environments requiring centralized control, mandatory locking (for binary assets, game studios), or where git's distributed model is a compliance concern, SVN remains a reasonable choice.

**SVN concepts that map to git**:
| SVN | Git |
|-----|-----|
| Repository | Repository |
| Working copy | Working tree |
| Commit | Commit |
| `svn checkout` | `git clone` |
| `svn update` | `git pull` |
| `svn commit` | `git commit` + `git push` |
| Revision number | SHA |
| Tag (copy to `/tags/`) | Tag |
| Branch (copy to `/branches/`) | Branch |

---

### Git (2005)

Created by Linus Torvalds for Linux kernel development after the previous VCS (BitKeeper) became unavailable. Designed around three requirements: distributed, fast, and integrity-preserving.

**Model**: distributed (every clone is a full repository), content-addressed storage (SHA hashes), directed acyclic graph of commits.

**Innovations**:
- Fully distributed: every clone is a complete repository with full history
- Staging area (index): precise control over what enters a commit
- Branching is a pointer (extremely cheap)
- Merging as a first-class operation with three-way merge
- Content-addressed storage: SHA integrity for all objects
- Offline operation: commit, branch, log, diff all work without network

**The distributed property changes everything**: developers have full history locally; forking is cheap; contributing to open-source is possible without write access to the original repository.

**Current ecosystem**: git is dominant. GitHub, GitLab, Bitbucket, and Gitea are all git hosts. CI/CD systems assume git. Most developer tooling is git-first.

---

### Jujutsu (2022)

See `references/jujutsu.md` for the full guide. Brief position in the lineage:

Built on top of git's storage model, designed to address git's rough edges (staging area, detached HEAD, merge conflicts as blocking states, no operation log). Not a replacement for git's network protocols or storage — a better interface to git's internals.

Represents the current frontier of VCS design thinking: what does a version control system look like when correctness (no data loss), recoverability (undo everything), and concurrent conflict handling are the primary design constraints?

---

## Non-Code Use Cases

Version control is appropriate for any content where:

1. Changes over time matter
2. The ability to compare versions has value
3. Reverting to a prior state is occasionally needed
4. Collaboration or multiple authors are involved

### Documents and Writing

Track drafts, review revision history, collaborate without email attachments:

```bash
# See what changed between drafts
git diff v1..v2 -- chapter-3.md
git diff --word-diff HEAD~3 -- proposal.md   # word-level diff for prose

# Recover a deleted section
git show HEAD~5:document.md | grep -A 20 "Section Title"
```

Word-level diffing (`--word-diff`) makes prose changes readable — git's default line-level diff is too coarse for document work.

**Recommended workflow**: commit after each meaningful editing session, not just at "save". "Restructured argument in section 3" as a commit message is more useful than "edits" — both to collaborators and to future-you trying to understand what changed.

### Configuration Files

Version infrastructure configs, dotfiles, application settings:

```bash
# Dotfiles repository
git init --bare $HOME/.dotfiles
alias dotfiles='git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
dotfiles add .vimrc .zshrc
dotfiles commit -m "chore: update zsh config with new aliases"
```

Versioning dotfiles enables disaster recovery (new machine setup), auditability (when did I add this setting?), and sharing (publish publicly for others to reference).

### Data Files (CSV, JSON, YAML)

Structured text formats diff well:

```bash
git diff HEAD~1 -- data/customers.csv      # see which rows changed
git log --follow --oneline -- config.yaml  # history of a config file
```

For large datasets, use `.gitignore` to exclude raw data files and version only schemas, transformation scripts, and small reference data.

### Note Vaults (Obsidian, etc.)

Personal knowledge management systems benefit significantly from version control:

- **History**: when did this note change? what was the original draft?
- **Sync**: git as a sync mechanism between devices (alternative to proprietary sync)
- **Backup**: remote repository as off-site backup
- **Branching**: experimental reorganizations can be branches, reverted if wrong
- **Collaboration**: shared vaults via PR workflow

```bash
# Typical vault commit rhythm
git add --all
git commit -m "notes: capture meeting with design team re: navigation changes"
git push
```

The commit discipline is looser for personal notes — frequent saves with brief messages ("daily notes 2025-04-01") are better than infrequent large commits. The goal is continuity and safety, not readable history.

### Binary Files and Large Assets

Git handles binary files poorly — diffs are not meaningful, and large files bloat the repository permanently (even after deletion). Use Git LFS (Large File Storage) for large binaries:

```bash
git lfs install
git lfs track "*.psd" "*.mp4" "*.zip"
git add .gitattributes
git add large-asset.psd
git commit -m "assets: add updated hero image"
```

LFS stores pointers in the repository and the actual content on a separate server. History remains fast; the asset is still versioned.

For assets that change frequently and where history is not needed, consider whether version control is the right tool — an asset management system or object storage with versioning may be more appropriate.

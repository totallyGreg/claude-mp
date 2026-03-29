# Branching Strategies

A branching strategy is a convention for how work moves from an idea to production. Choose based on team size, release cadence, and deployment model — not based on what's fashionable.

## The Decision Tree

```
Single developer, continuous deployment?
  → Trunk-based (simplified: commit directly to main)

Small team, fast iteration, continuous deployment?
  → Trunk-based development

Team with code review requirements?
  → GitHub Flow (short-lived feature branches + PR)

Software with multiple supported versions in production?
  → Release branching (variant of GitHub Flow)

Complex release cadence, large team, strict QA gates?
  → Git-flow (evaluate carefully — high overhead)

Open-source with async contributors?
  → Fork + PR model (GitHub Flow at the contributor level)
```

## Trunk-Based Development (Default Recommendation)

A single integration branch (`main` or `trunk`). All developers integrate to it frequently — at minimum daily. Feature branches are short-lived (hours to a few days).

```
main: ──●──●──●──●──●──●──●──
          ↑     ↑     ↑
      feature branches
      (merged same day or next)
```

### Why it's the default

- Forces continuous integration, catches conflicts early
- No "merge hell" from long-lived diverged branches
- Simple mental model: one canonical truth
- Deployment is always from main; no release coordination overhead
- Supports feature flags for incomplete work better than long-lived branches

### Feature flags instead of long branches

When a feature takes weeks, use a flag rather than a branch:

```python
if feature_flags.enabled("new-checkout-flow", user):
    return new_checkout(cart)
return legacy_checkout(cart)
```

The code ships to production in each commit, inactive behind the flag. When ready, flip the flag. When retired, delete the dead code path.

### When to avoid trunk-based

- Regulated environments requiring change approval before merge (use release branching instead)
- Open-source projects where contributors are external and async (use fork model)
- Libraries with long-term version support obligations (use release branches)

## GitHub Flow

Simple two-tier model: `main` is always deployable; work happens in short-lived feature branches that are reviewed and merged via pull request.

```
main:          ──●────────────────●────────────●──
                  \              /  \          /
feature/login:    ●──●──●──review   ●──●──review
```

### Rules

1. Anything in `main` is deployable
2. Create branches from `main` with descriptive names (`feature/user-auth`, `fix/null-pointer-on-login`)
3. Commit to the branch regularly
4. Open a pull request to start discussion (can be draft/WIP)
5. Merge only after review and passing CI
6. Deploy immediately after merge

### Branch naming conventions

```
feature/<description>     # new capability
fix/<description>         # bug fix
docs/<description>        # documentation only
refactor/<description>    # structural change, no behavior change
experiment/<name>-<date>  # exploratory, may be discarded
chore/<description>       # tooling, dependencies
```

Use kebab-case. Keep names short but specific: `fix/login-redirect-loop` not `fix/bug`.

## Release Branching

For software that ships discrete versions (mobile apps, libraries, desktop software), release branches provide a stable track per version.

```
main:      ──●──●──●──●──●──●──●──
               \           \
release/1.0:   ●──●(patch) ●──(1.0.1 tag)
release/2.0:               ●──●(patch)──(2.0.1 tag)
```

### Rules

- `main` receives all new development
- Release branches are cut from `main` at the point a version is feature-complete
- Only bug fixes go into release branches — never new features
- Bug fixes land on `main` first, then are cherry-picked to affected release branches
- Tag releases on the release branch: `git tag v1.0.1 -m "Patch: fix login crash"`

### Cherry-pick discipline for release branches

```bash
# Fix on main first
git switch main
git commit -m "fix(auth): prevent null dereference on expired token"

# Cherry-pick to affected release branches
git switch release/1.0
git cherry-pick <sha>
git tag v1.0.1 -m "fix: prevent null dereference on expired token"
```

Never develop directly on a release branch. Always fix forward on `main` first.

## Git-Flow

A heavyweight model with two permanent branches (`main` and `develop`) plus three categories of supporting branches (feature, release, hotfix).

```
main:     ──────────────────●─────────────────────●──
                           /↑\                   /↑\
develop:  ──●──●──●──●──●──  ●──●──●──●──●──●──  ●──
              \       /         \       /
feature:      ●──●──●            ●──●──●
                        release/1.0: ●──●(QA fixes)──●
```

### When git-flow is appropriate

- Large teams with dedicated QA stages
- Software with scheduled, infrequent releases
- Environments requiring explicit release artifacts and change audits
- Multi-team coordination where `develop` acts as an integration buffer

### When git-flow adds cost without value

Most teams. The `develop` branch creates a permanent divergence from `main`, doubles the branches that need updating, and adds coordination overhead that trunk-based development eliminates entirely.

If you find yourself needing git-flow, first ask whether feature flags and release branches achieve the same goal with less ceremony.

## Long-Running Experiment Branches

For exploratory work that may be discarded:

```
experiment/<name>-<date>     # e.g. experiment/vector-search-2025-03
```

Rules for experiment branches:
- Never merge directly to `main` without review
- Use worktrees for parallel experiments (see `references/worktrees-experiments.md`)
- Set an explicit expiry: if not merged within N weeks, evaluate and delete
- Document the hypothesis in the first commit message

## Protecting Main

Configure branch protection regardless of which strategy is used:

```
Require pull request reviews before merging: 1 reviewer minimum
Require status checks to pass before merging: CI, linting, tests
Restrict who can push directly to main
Do not allow force pushes
```

For solo work, at minimum: require CI to pass. Even one failing check caught before merge is worth the setup.

## Merging Back: The Integration Commit

When a feature branch merges into main, the merge commit message matters:

```
feat(payments): add Stripe webhook signature verification (#234)

Validates webhook payloads using HMAC-SHA256 before processing.
Rejects replayed events older than 5 minutes.

Closes #234.
```

This is visible in `git log --merges` and in GitHub's merge history. Write it as documentation, not bookkeeping.

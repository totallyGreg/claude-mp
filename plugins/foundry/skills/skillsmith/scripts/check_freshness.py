#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Generic Reference Freshness Checker.

Scans any skill's references/ for provenance frontmatter and reports staleness.
Checks each source type (web, github, gitlab, slack, plugin) for activity
since last_verified.

Usage:
    uv run check_freshness.py [OPTIONS] [SKILL_PATH]

Options:
    --since DATE         Override last_verified with this date (YYYY-MM-DD)
    --threshold-days N   Days before a reference is stale (default: 90)
    --probe              HTTP-check web source URLs
    --full-audit         Show all source activity regardless of last_verified
    --format json        Machine-readable JSON output
    --verbose            Show detailed per-source check results

Output: Markdown freshness report to stdout (or JSON with --format json).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path


DEFAULT_THRESHOLD_DAYS = 90


def parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    import yaml
    return yaml.safe_load(text[3:end]) or {}


def parse_date(date_val) -> date | None:
    """Parse date from YAML (may be date object) or string."""
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if not isinstance(date_val, str) or not date_val:
        return None
    try:
        return datetime.strptime(date_val.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def check_web_source(source: dict) -> dict:
    """HTTP HEAD check on a web URL. Returns status info."""
    url = source.get("url", "")
    if not url:
        return {"status": "skip", "reason": "no url"}
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "10", "-L", url],
            capture_output=True, text=True, timeout=15,
        )
        code = int(result.stdout.strip())
        reachable = 200 <= code < 400
        return {"status": "ok" if reachable else "unreachable", "http_code": code, "url": url}
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        return {"status": "error", "reason": "curl failed or timed out", "url": url}


def check_github_source(source: dict, since: date | None = None,
                        detailed: bool = False) -> dict:
    """Check GitHub repo activity via gh CLI."""
    repo = source.get("repo", "")
    if not repo:
        return {"status": "skip", "reason": "no repo"}

    paths = source.get("paths", [])
    result_info: dict = {"status": "ok", "repo": repo, "commits_since": 0,
                         "latest_commit": None, "changed_files": []}

    try:
        subprocess.run(["gh", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        return {"status": "warn", "reason": "gh CLI not installed", "repo": repo}

    # Check repo-level or path-level commits
    if since and paths:
        since_str = since.isoformat()
        total_commits = 0
        for path in paths:
            try:
                r = subprocess.run(
                    ["gh", "api",
                     f"repos/{repo}/commits?since={since_str}T00:00:00Z"
                     f"&path={path}&per_page=100"],
                    capture_output=True, text=True, timeout=15,
                )
                if r.returncode == 0:
                    commits = json.loads(r.stdout)
                    total_commits += len(commits)
                    if detailed:
                        for c in commits:
                            title = c["commit"]["message"].split("\n")[0]
                            cdate = c["commit"]["committer"]["date"][:10]
                            result_info["changed_files"].append(
                                f"{path} — {cdate}: {title}"
                            )
            except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
                pass
        result_info["commits_since"] = total_commits
    elif since:
        since_str = since.isoformat()
        try:
            r = subprocess.run(
                ["gh", "api",
                 f"repos/{repo}/commits?since={since_str}T00:00:00Z&per_page=1"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                commits = json.loads(r.stdout)
                result_info["commits_since"] = len(commits)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

    # Get latest commit date
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits?per_page=1"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            commits = json.loads(r.stdout)
            if commits:
                result_info["latest_commit"] = commits[0]["commit"]["committer"]["date"][:10]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        pass

    return result_info


def check_gitlab_source(source: dict, since: date | None = None,
                        detailed: bool = False) -> dict:
    """Check GitLab repo activity via glab CLI."""
    project_id = source.get("project_id")
    if not project_id:
        return {"status": "skip", "reason": "no project_id"}

    paths = source.get("paths", [])
    result_info: dict = {"status": "ok", "project_id": project_id, "commits_since": 0,
                         "latest_commit": None, "changed_files": []}

    try:
        subprocess.run(["glab", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        return {"status": "warn", "reason": "glab CLI not installed", "project_id": project_id}

    if since and paths:
        since_str = since.isoformat()
        total_commits = 0
        for path in paths:
            try:
                r = subprocess.run(
                    ["glab", "api",
                     f"projects/{project_id}/repository/commits?since={since_str}T00:00:00Z"
                     f"&path={path}&per_page=100"],
                    capture_output=True, text=True, timeout=15,
                )
                if r.returncode == 0:
                    commits = json.loads(r.stdout)
                    total_commits += len(commits)
                    if detailed:
                        for c in commits:
                            title = c.get("title", "")
                            cdate = c.get("committed_date", "")[:10]
                            result_info["changed_files"].append(
                                f"{path} — {cdate}: {title}"
                            )
            except (subprocess.TimeoutExpired, json.JSONDecodeError):
                pass
        result_info["commits_since"] = total_commits
    elif since:
        since_str = since.isoformat()
        try:
            r = subprocess.run(
                ["glab", "api",
                 f"projects/{project_id}/repository/commits?since={since_str}T00:00:00Z&per_page=1"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                commits = json.loads(r.stdout)
                result_info["commits_since"] = len(commits)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

    try:
        r = subprocess.run(
            ["glab", "api", f"projects/{project_id}/repository/commits?per_page=1"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            commits = json.loads(r.stdout)
            if commits:
                result_info["latest_commit"] = commits[0].get("committed_date", "")[:10]
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    return result_info


def check_slack_source(source: dict, since: date | None = None) -> dict:
    """Check Slack channel for messages since last_verified."""
    channel_id = source.get("channel_id", "")
    if not channel_id:
        return {"status": "skip", "reason": "no channel_id"}

    token = os.environ.get("SLACK_USER_TOKEN", "")
    if not token:
        return {"status": "warn", "reason": "SLACK_USER_TOKEN not set", "channel_id": channel_id}

    params: dict[str, str | int] = {"channel": channel_id, "limit": 50}
    if since:
        params["oldest"] = str(int(datetime.combine(since, datetime.min.time()).timestamp()))

    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/conversations.history",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    body: dict = {}
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    if attempt == 0:
                        time.sleep(retry_after)
                        continue
                    return {"status": "error", "reason": "rate limited", "channel_id": channel_id}
                body = json.loads(resp.read().decode("utf-8"), strict=False)
        except Exception as e:
            return {"status": "error", "reason": str(e), "channel_id": channel_id}
        break

    if not body.get("ok"):
        return {"status": "error", "reason": body.get("error", "unknown"), "channel_id": channel_id}

    message_count = sum(
        1 for msg in body.get("messages", [])
        if msg.get("subtype") not in ("channel_join", "channel_leave")
        and msg.get("text", "").strip()
    )

    return {"status": "ok", "channel_id": channel_id, "messages_since": message_count}


def check_plugin_source(source: dict) -> dict:
    """Check installed plugin version vs known_version."""
    plugin_name = source.get("name", "")
    if not plugin_name:
        return {"status": "skip", "reason": "no plugin name"}

    known_version = source.get("known_version", "")
    plugins_dir = Path.home() / ".claude" / "plugins"

    # Search installed plugins and cache for matching plugin
    installed_version = None
    search_dirs = [plugins_dir]
    cache_dir = plugins_dir / "cache"
    if cache_dir.is_dir():
        search_dirs.append(cache_dir)

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for plugin_json in search_dir.rglob("plugin.json"):
            try:
                data = json.loads(plugin_json.read_text())
                if data.get("name", "").lower() == plugin_name.lower():
                    installed_version = data.get("version", "unknown")
                    break
            except (json.JSONDecodeError, OSError):
                continue
        if installed_version:
            break

    if not installed_version:
        return {"status": "warn", "reason": f"plugin '{plugin_name}' not installed",
                "plugin": plugin_name}

    drift = False
    if known_version and installed_version != known_version:
        drift = True

    return {
        "status": "drift" if drift else "ok",
        "plugin": plugin_name,
        "known_version": known_version or "unset",
        "installed_version": installed_version,
    }


def scan_skill_references(skill_path: Path) -> list[dict]:
    """Scan a skill's references/ directory for provenance-tracked files."""
    refs_dir = skill_path / "references"
    if not refs_dir.is_dir():
        return []

    results = []
    for ref_path in sorted(refs_dir.glob("*.md")):
        fm = parse_frontmatter(ref_path)
        last_verified = parse_date(fm.get("last_verified"))
        sources = fm.get("sources", [])

        if not sources and not last_verified:
            continue

        results.append({
            "file": ref_path.name,
            "path": str(ref_path),
            "last_verified": last_verified,
            "sources": sources,
        })

    return results


def check_reference(ref: dict, today: date, threshold_days: int,
                    since_override: date | None = None,
                    probe: bool = False, full_audit: bool = False) -> dict:
    """Check a single reference's freshness against all its sources."""
    last_verified = ref["last_verified"]
    since = since_override or last_verified

    age_days = (today - last_verified).days if last_verified else None
    is_stale = age_days is not None and age_days > threshold_days
    never_verified = last_verified is None and ref["sources"]

    source_results = []
    has_activity = False

    for source in ref["sources"]:
        src_type = source.get("type", "unknown")
        result: dict = {"type": src_type, "description": source.get("description", "")}

        if src_type == "web":
            if probe:
                result.update(check_web_source(source))
            else:
                result["status"] = "skipped"
                result["reason"] = "use --probe to check URLs"
        elif src_type == "github":
            result.update(check_github_source(source, since=since, detailed=full_audit))
            if result.get("commits_since", 0) > 0:
                has_activity = True
        elif src_type == "gitlab":
            result.update(check_gitlab_source(source, since=since, detailed=full_audit))
            if result.get("commits_since", 0) > 0:
                has_activity = True
        elif src_type == "slack":
            result.update(check_slack_source(source, since=since))
            if result.get("messages_since", 0) > 0:
                has_activity = True
        elif src_type == "plugin":
            result.update(check_plugin_source(source))
            if result.get("status") == "drift":
                has_activity = True
        else:
            result["status"] = "unknown"
            result["reason"] = f"unsupported source type: {src_type}"

        source_results.append(result)

    return {
        "file": ref["file"],
        "last_verified": last_verified.isoformat() if last_verified else None,
        "age_days": age_days,
        "is_stale": is_stale or never_verified,
        "never_verified": never_verified,
        "has_upstream_activity": has_activity,
        "sources": source_results,
    }


def calculate_freshness_score(results: list[dict]) -> int:
    """Calculate freshness score as percentage of non-stale tracked references."""
    if not results:
        return 100
    fresh_count = sum(1 for r in results if not r["is_stale"])
    return int((fresh_count / len(results)) * 100)


def format_markdown_report(results: list[dict], score: int, today: date,
                           threshold_days: int) -> str:
    """Format results as a markdown freshness report."""
    lines = [
        "# Reference Freshness Report",
        f"\nGenerated: {today}",
        f"Staleness threshold: {threshold_days} days",
        f"Freshness score: {score}/100",
        f"Tracked references: {len(results)}",
        "",
    ]

    stale_refs = [r for r in results if r["is_stale"]]
    fresh_refs = [r for r in results if not r["is_stale"]]

    if stale_refs:
        lines.append("## Stale References\n")
        for r in stale_refs:
            if r["never_verified"]:
                lines.append(f"- **{r['file']}** — never verified (has sources but no last_verified)")
            else:
                lines.append(f"- **{r['file']}** — last verified {r['last_verified']} "
                             f"({r['age_days']} days ago)")
        lines.append("")

    if fresh_refs:
        lines.append("## Fresh References\n")
        for r in fresh_refs:
            lines.append(f"- {r['file']} — last verified {r['last_verified']} "
                         f"({r['age_days']} days ago)")
        lines.append("")

    activity_refs = [r for r in results if r["has_upstream_activity"]]
    if activity_refs:
        lines.append("## Upstream Activity Detected\n")
        for r in activity_refs:
            lines.append(f"### {r['file']}\n")
            for src in r["sources"]:
                if src.get("commits_since", 0) > 0:
                    lines.append(f"- **{src['type']}** ({src.get('description', '')}): "
                                 f"{src['commits_since']} commits since {r['last_verified']}")
                    for entry in src.get("changed_files", []):
                        lines.append(f"  - {entry}")
                elif src.get("messages_since", 0) > 0:
                    lines.append(f"- **slack** ({src.get('description', '')}): "
                                 f"{src['messages_since']} messages since {r['last_verified']}")
                elif src.get("status") == "drift":
                    lines.append(f"- **plugin** ({src.get('description', '')}): "
                                 f"installed v{src.get('installed_version')} "
                                 f"vs known v{src.get('known_version')}")
            lines.append("")

    # Warnings
    warnings = []
    for r in results:
        for src in r["sources"]:
            if src.get("status") == "warn":
                warnings.append(f"- {r['file']}: {src['type']} — {src.get('reason', '')}")
            elif src.get("status") == "error":
                warnings.append(f"- {r['file']}: {src['type']} — {src.get('reason', '')}")
            elif src.get("status") == "unreachable":
                warnings.append(f"- {r['file']}: web — {src.get('url', '')} "
                                f"(HTTP {src.get('http_code', '?')})")

    if warnings:
        lines.append("## Warnings\n")
        for w in warnings:
            lines.append(w)
        lines.append("")

    return "\n".join(lines)


def format_json_output(results: list[dict], score: int, today: date,
                       threshold_days: int) -> str:
    """Format results as JSON for programmatic consumption."""
    output = {
        "generated": today.isoformat(),
        "threshold_days": threshold_days,
        "score": score,
        "tracked_references": len(results),
        "stale_count": sum(1 for r in results if r["is_stale"]),
        "references": results,
    }
    return json.dumps(output, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(
        description="Generic reference freshness checker for AgentSkills"
    )
    parser.add_argument("skill_path", nargs="?", default=".",
                        help="Path to skill directory (default: current directory)")
    parser.add_argument("--since", type=str, default=None,
                        help="Override last_verified with this date (YYYY-MM-DD)")
    parser.add_argument("--threshold-days", type=int, default=DEFAULT_THRESHOLD_DAYS,
                        help=f"Days before a reference is stale (default: {DEFAULT_THRESHOLD_DAYS})")
    parser.add_argument("--probe", action="store_true",
                        help="HTTP-check web source URLs")
    parser.add_argument("--full-audit", action="store_true",
                        help="Show all source activity regardless of last_verified cutoff")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed per-source check results")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()

    # Auto-detect: if given a references/ dir, go up one level
    if skill_path.name == "references" and skill_path.is_dir():
        skill_path = skill_path.parent

    # Validate skill path
    if not (skill_path / "references").is_dir():
        if args.format == "json":
            print(json.dumps({"error": f"No references/ directory at {skill_path}",
                              "score": 100, "tracked_references": 0}))
        else:
            print(f"No references/ directory found at {skill_path}", file=sys.stderr)
            print("Score: 100 (no provenance-tracked references)")
        sys.exit(0)

    since_override = parse_date(args.since) if args.since else None
    today = date.today()

    # Scan references
    tracked_refs = scan_skill_references(skill_path)

    if not tracked_refs:
        if args.format == "json":
            print(json.dumps({"score": 100, "tracked_references": 0,
                              "message": "No provenance-tracked references found"}))
        else:
            print("No provenance-tracked references found.")
            print("Score: 100 (neutral — opt-in provenance not configured)")
        sys.exit(0)

    if args.verbose:
        print(f"Found {len(tracked_refs)} provenance-tracked references", file=sys.stderr)

    # Check each reference
    results = []
    for ref in tracked_refs:
        if args.verbose:
            print(f"  Checking {ref['file']}...", file=sys.stderr)
        result = check_reference(
            ref, today, args.threshold_days,
            since_override=since_override,
            probe=args.probe,
            full_audit=args.full_audit,
        )
        results.append(result)

    score = calculate_freshness_score(results)

    if args.format == "json":
        print(format_json_output(results, score, today, args.threshold_days))
    else:
        print(format_markdown_report(results, score, today, args.threshold_days))


if __name__ == "__main__":
    main()

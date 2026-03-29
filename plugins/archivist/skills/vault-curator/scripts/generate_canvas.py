#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Generate JSON Canvas files showing note relationships within a scope.

Scans notes in a vault scope, extracts wikilinks between them, and produces
a .canvas file with file nodes and edges. Uses grid layout with 50-node cap;
clusters overflow into group nodes.

Usage:
    uv run generate_canvas.py <vault-path> --scope <path> [options]

Options:
    --scope <path>       Vault-relative folder to scan (required)
    --output <name>      Output filename (default: _knowledge-map-YYYY-MM-DD.canvas)
    --max-nodes <n>      Maximum nodes before clustering (default: 50)
    --dry-run            Show what would be generated without writing

Returns:
    JSON with generation result:
    {
        "status": "success",
        "canvas_path": "Work/Projects/_knowledge-map-2026-02-16.canvas",
        "nodes": 35,
        "edges": 42,
        "clusters": 0
    }
"""

import sys
import json
import math
import re
import secrets
from datetime import date
from pathlib import Path
from typing import Any
from collections import defaultdict

import frontmatter


# --- Layout constants ---
NODE_WIDTH = 300
NODE_HEIGHT = 120
NODE_SPACING_X = 80
NODE_SPACING_Y = 60
GROUP_PADDING = 30
GROUP_LABEL_HEIGHT = 40


def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/System']

    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")

    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    return vault_path


def gen_id() -> str:
    """Generate a 16-character lowercase hex ID per JSON Canvas spec."""
    return secrets.token_hex(8)


def extract_wikilinks(content: str) -> set[str]:
    """Extract wikilink targets from note content."""
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    links = set()
    for match in re.finditer(pattern, content):
        target = match.group(1).strip()
        if target:
            links.add(target)
    return links


def load_scope_notes(vault_path: Path, scope: str) -> list[dict[str, Any]]:
    """Load notes within scope with metadata and wikilinks."""
    search_root = vault_path / scope

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    skip_dirs = {'templates', 'Templates', '_templates', '.obsidian', '.trash'}
    notes = []

    for md_file in search_root.rglob("*.md"):
        rel_path = str(md_file.relative_to(vault_path))

        if any(part in skip_dirs for part in md_file.relative_to(vault_path).parts):
            continue

        try:
            post = frontmatter.load(md_file)
            metadata = dict(post.metadata)
            title = metadata.get('title') or metadata.get('name') or md_file.stem
            file_class = metadata.get('fileClass') or metadata.get('fileclass', '')

            notes.append({
                "path": rel_path,
                "title": str(title),
                "stem": md_file.stem,
                "file_class": str(file_class),
                "folder": str(md_file.parent.relative_to(vault_path)),
                "links": extract_wikilinks(post.content),
            })
        except Exception:
            continue

    return notes


def build_edges(notes: list[dict]) -> list[tuple[int, int]]:
    """Build edge list from wikilinks between notes in scope.

    Returns list of (source_index, target_index) tuples.
    """
    # Map note stems (case-insensitive) to indices for wikilink resolution
    stem_to_idx: dict[str, int] = {}
    for i, note in enumerate(notes):
        stem_to_idx[note["stem"].lower()] = i

    edges = []
    seen = set()

    for i, note in enumerate(notes):
        for link_target in note["links"]:
            # Wikilinks use the note name (stem), not the full path
            target_key = link_target.lower()
            if target_key in stem_to_idx:
                j = stem_to_idx[target_key]
                if i != j:
                    pair = (min(i, j), max(i, j))
                    if pair not in seen:
                        seen.add(pair)
                        edges.append((i, j))

    return edges


def cluster_notes(
    notes: list[dict],
    edges: list[tuple[int, int]],
    max_nodes: int,
) -> tuple[list[dict], list[tuple[int, int]], list[dict]]:
    """If notes exceed max_nodes, cluster by folder into groups.

    Returns (top_notes, top_edges, clusters) where:
    - top_notes: individual notes or cluster representatives
    - top_edges: edges between top-level items
    - clusters: list of {label, notes, folder} for group nodes
    """
    if len(notes) <= max_nodes:
        return notes, edges, []

    # Group notes by immediate subfolder within scope
    folder_groups: dict[str, list[int]] = defaultdict(list)
    for i, note in enumerate(notes):
        folder_groups[note["folder"]].append(i)

    # Sort folders by note count descending
    sorted_folders = sorted(folder_groups.items(), key=lambda x: -len(x[1]))

    # Keep individual notes until we hit max_nodes, cluster the rest
    top_notes = []
    clusters = []
    note_to_top: dict[int, int] = {}  # original index -> top-level index

    budget = max_nodes
    for folder, indices in sorted_folders:
        if len(indices) <= 3 and budget >= len(indices):
            # Small folder: keep individual notes
            for idx in indices:
                top_idx = len(top_notes)
                note_to_top[idx] = top_idx
                top_notes.append(notes[idx])
                budget -= 1
        else:
            # Cluster into a group
            cluster_idx = len(top_notes)
            folder_label = Path(folder).name or folder
            cluster = {
                "label": f"{folder_label} ({len(indices)} notes)",
                "folder": folder,
                "notes": [notes[i] for i in indices],
            }
            clusters.append(cluster)
            # All notes in this folder map to the cluster's representative
            for idx in indices:
                note_to_top[idx] = cluster_idx
            # Add a representative entry
            top_notes.append({
                "path": f"_cluster_{folder_label}",
                "title": folder_label,
                "stem": f"_cluster_{folder_label}",
                "file_class": "cluster",
                "folder": folder,
                "links": set(),
                "_is_cluster": True,
                "_cluster_index": len(clusters) - 1,
            })
            budget -= 1

        if budget <= 0:
            break

    # Remap edges
    top_edges = []
    seen = set()
    for src, dst in edges:
        if src in note_to_top and dst in note_to_top:
            new_src = note_to_top[src]
            new_dst = note_to_top[dst]
            if new_src != new_dst:
                pair = (min(new_src, new_dst), max(new_src, new_dst))
                if pair not in seen:
                    seen.add(pair)
                    top_edges.append((new_src, new_dst))

    return top_notes, top_edges, clusters


def grid_layout(count: int) -> list[tuple[int, int]]:
    """Calculate grid positions for n nodes. Returns list of (x, y) tuples."""
    if count == 0:
        return []

    cols = math.ceil(math.sqrt(count))
    positions = []

    for i in range(count):
        row = i // cols
        col = i % cols
        x = col * (NODE_WIDTH + NODE_SPACING_X)
        y = row * (NODE_HEIGHT + NODE_SPACING_Y)
        positions.append((x, y))

    return positions


def fileclass_color(file_class: str) -> str | None:
    """Map fileClass to a canvas preset color for visual distinction."""
    mapping = {
        'meeting': '2',    # Orange
        'person': '5',     # Cyan
        'project': '4',    # Green
        'company': '6',    # Purple
        'moc': '3',        # Yellow
        'log': '1',        # Red
        'cluster': '6',    # Purple for clusters
    }
    return mapping.get(file_class.lower()) if file_class else None


def generate_canvas(
    notes: list[dict],
    edges: list[tuple[int, int]],
    clusters: list[dict],
) -> dict:
    """Generate JSON Canvas data structure."""
    positions = grid_layout(len(notes))
    nodes = []
    node_ids = []

    for note, (x, y) in zip(notes, positions):
        node_id = gen_id()
        node_ids.append(node_id)

        if note.get("_is_cluster"):
            # Group node for clustered folders
            cluster = clusters[note["_cluster_index"]]
            sub_count = len(cluster["notes"])
            # Size group to roughly contain sub-notes
            sub_cols = math.ceil(math.sqrt(sub_count))
            sub_rows = math.ceil(sub_count / max(sub_cols, 1))
            group_w = sub_cols * (NODE_WIDTH + NODE_SPACING_X) + GROUP_PADDING * 2
            group_h = sub_rows * (NODE_HEIGHT + NODE_SPACING_Y) + GROUP_PADDING * 2 + GROUP_LABEL_HEIGHT

            group_node = {
                "id": node_id,
                "type": "group",
                "x": x,
                "y": y,
                "width": max(group_w, NODE_WIDTH + GROUP_PADDING * 2),
                "height": max(group_h, NODE_HEIGHT + GROUP_PADDING * 2 + GROUP_LABEL_HEIGHT),
                "label": cluster["label"],
            }
            color = fileclass_color("cluster")
            if color:
                group_node["color"] = color
            nodes.append(group_node)

            # Add sub-notes inside the group
            sub_positions = grid_layout(sub_count)
            for sub_note, (sx, sy) in zip(cluster["notes"], sub_positions):
                sub_id = gen_id()
                sub_node = {
                    "id": sub_id,
                    "type": "file",
                    "x": x + GROUP_PADDING + sx,
                    "y": y + GROUP_PADDING + GROUP_LABEL_HEIGHT + sy,
                    "width": NODE_WIDTH,
                    "height": NODE_HEIGHT,
                    "file": sub_note["path"],
                }
                color = fileclass_color(sub_note.get("file_class", ""))
                if color:
                    sub_node["color"] = color
                nodes.append(sub_node)
        else:
            # Regular file node
            node = {
                "id": node_id,
                "type": "file",
                "x": x,
                "y": y,
                "width": NODE_WIDTH,
                "height": NODE_HEIGHT,
                "file": note["path"],
            }
            color = fileclass_color(note.get("file_class", ""))
            if color:
                node["color"] = color
            nodes.append(node)

    # Generate edges
    canvas_edges = []
    for src, dst in edges:
        if src < len(node_ids) and dst < len(node_ids):
            canvas_edges.append({
                "id": gen_id(),
                "fromNode": node_ids[src],
                "fromSide": "right",
                "toNode": node_ids[dst],
                "toSide": "left",
            })

    return {"nodes": nodes, "edges": canvas_edges}


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: generate_canvas.py <vault-path> --scope <path> [--output <name>] [--max-nodes <n>] [--dry-run]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    scope = None
    output_name = None
    max_nodes = 50
    dry_run = False

    # Parse args
    i = 1
    while i < len(args):
        if args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_name = args[i + 1]
            i += 2
        elif args[i] == "--max-nodes" and i + 1 < len(args):
            max_nodes = int(args[i + 1])
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    if not scope:
        print(json.dumps({
            "status": "error",
            "error": "Must specify --scope <path>",
        }))
        sys.exit(1)

    try:
        vault_path = validate_vault_path(vault_path_str)

        # Default output name
        if not output_name:
            output_name = f"_knowledge-map-{date.today().isoformat()}.canvas"
        if not output_name.endswith(".canvas"):
            output_name += ".canvas"

        output_path = vault_path / scope / output_name
        rel_output = str(output_path.relative_to(vault_path))

        if dry_run:
            notes = load_scope_notes(vault_path, scope)
            edges = build_edges(notes)
            print(json.dumps({
                "status": "dry_run",
                "scope": scope,
                "total_notes": len(notes),
                "total_edges": len(edges),
                "max_nodes": max_nodes,
                "would_cluster": len(notes) > max_nodes,
                "output_path": rel_output,
                "message": "Would generate canvas with these parameters",
            }, indent=2))
            return

        # Load and process
        notes = load_scope_notes(vault_path, scope)

        if not notes:
            print(json.dumps({
                "status": "success",
                "scope": scope,
                "total_notes": 0,
                "message": "No markdown files found in scope. Try broadening the scope.",
            }, indent=2))
            return

        edges = build_edges(notes)

        if not edges and len(notes) > 1:
            # No wikilinks between notes — still generate but note it
            pass

        # Cluster if needed
        top_notes, top_edges, clusters = cluster_notes(notes, edges, max_nodes)

        # Generate canvas
        canvas_data = generate_canvas(top_notes, top_edges, clusters)

        # Handle existing canvas
        if output_path.exists():
            # Append date suffix to avoid overwrite
            stem = output_path.stem
            suffix = 1
            while output_path.exists():
                output_path = output_path.parent / f"{stem}-{suffix}.canvas"
                suffix += 1
            rel_output = str(output_path.relative_to(vault_path))

        # Write canvas file
        with open(output_path, 'w') as f:
            json.dump(canvas_data, f, indent=2)

        result = {
            "status": "success",
            "canvas_path": rel_output,
            "scope": scope,
            "nodes": len(canvas_data["nodes"]),
            "edges": len(canvas_data["edges"]),
            "clusters": len(clusters),
            "total_notes_scanned": len(notes),
        }

        if not edges:
            result["message"] = "No wikilinks found between notes in scope. Canvas shows notes without connections. Consider adding [[wikilinks]] to connect related notes."

        if clusters:
            result["message"] = f"Large scope ({len(notes)} notes) clustered into {len(clusters)} group(s) to stay under {max_nodes}-node cap."

        print(json.dumps(result, indent=2, default=str))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()

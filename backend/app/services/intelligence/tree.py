"""Build a compact repository tree (max depth / max nodes)."""
from __future__ import annotations

from collections import deque
from pathlib import Path

from app.services.intelligence.detectors import _IGNORE_DIRS

_MAX_DEPTH = 4
_MAX_NODES = 300


def build_tree(root: Path, max_depth: int = _MAX_DEPTH, max_nodes: int = _MAX_NODES) -> dict:
    """Return a nested dict representing the directory tree.

    Traversal is breadth-first so every top-level directory is captured before the
    node budget is spent descending into any single subtree (a depth-first walk would
    let an early, large sibling — e.g. "backend" sorting before "frontend" — exhaust
    the whole budget and make later siblings vanish from the scan entirely).
    """
    root_node: dict = {"name": root.name, "type": "dir", "children": []}
    count = 1
    queue: deque[tuple[Path, dict, int]] = deque([(root, root_node, 0)])

    while queue:
        path, node, depth = queue.popleft()
        if depth >= max_depth:
            continue
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            continue
        for entry in entries:
            if entry.name in _IGNORE_DIRS:
                continue
            if count >= max_nodes:
                if not node["children"] or node["children"][-1].get("type") != "truncated":
                    node["children"].append({"name": "...", "type": "truncated"})
                continue
            if entry.is_dir():
                child: dict = {"name": entry.name, "type": "dir", "children": []}
                node["children"].append(child)
                count += 1
                queue.append((entry, child, depth + 1))
            else:
                node["children"].append({"name": entry.name, "type": "file"})
                count += 1

    return root_node


def tree_to_text(node: dict, indent: int = 0) -> str:
    """Convert tree dict to a human-readable indented string."""
    prefix = "  " * indent
    lines = [f"{prefix}{'📁 ' if node['type'] == 'dir' else '📄 '}{node['name']}"]
    for child in node.get("children", []):
        lines.append(tree_to_text(child, indent + 1))
    return "\n".join(lines)

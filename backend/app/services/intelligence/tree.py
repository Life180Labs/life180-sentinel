"""Build a compact repository tree (max depth / max nodes)."""
from __future__ import annotations

from pathlib import Path

from app.services.intelligence.detectors import _IGNORE_DIRS

_MAX_DEPTH = 4
_MAX_NODES = 300


def build_tree(root: Path, max_depth: int = _MAX_DEPTH, max_nodes: int = _MAX_NODES) -> dict:
    """Return a nested dict representing the directory tree."""
    counter = [0]

    def _walk(path: Path, depth: int) -> dict | None:
        if depth > max_depth or counter[0] >= max_nodes:
            return None
        node: dict = {"name": path.name, "type": "dir", "children": []}
        counter[0] += 1
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return node
        for entry in entries:
            if entry.name in _IGNORE_DIRS:
                continue
            if counter[0] >= max_nodes:
                node["children"].append({"name": "...", "type": "truncated"})
                break
            if entry.is_dir():
                child = _walk(entry, depth + 1)
                if child:
                    node["children"].append(child)
            else:
                node["children"].append({"name": entry.name, "type": "file"})
                counter[0] += 1
        return node

    tree = _walk(root, 0)
    return tree or {"name": root.name, "type": "dir", "children": []}


def tree_to_text(node: dict, indent: int = 0) -> str:
    """Convert tree dict to a human-readable indented string."""
    prefix = "  " * indent
    lines = [f"{prefix}{'📁 ' if node['type'] == 'dir' else '📄 '}{node['name']}"]
    for child in node.get("children", []):
        lines.append(tree_to_text(child, indent + 1))
    return "\n".join(lines)

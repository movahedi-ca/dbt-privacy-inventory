#!/usr/bin/env python3
"""export_graph.py — manifest.json -> public_graph.json (allowlist only).

Reads the raw dbt manifest and emits the minimal public graph:
nodes (id, name, type, description, depends_on, tags) and edges
(parent -> child). Nothing else leaves the build plane: no manifest,
no catalog, no compiled SQL, no source file paths, no usernames,
no environment values, no row samples, no warehouse names.
Labels are emitted as plain text; consumers must encode them.
Enforces config/public-artifact-policy.yml limits.
"""
import argparse, json, sys

MAX_NODES = 500
MAX_EDGES = 2000
MAX_DEPTH = 10
MAX_LABEL_CHARS = 200

def label(value, fallback):
    text = (value or fallback or "").strip()
    return text[:MAX_LABEL_CHARS]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.manifest) as f:
        manifest = json.load(f)
    nodes = {}
    edges = []
    for key, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") not in ("model", "seed", "test", "snapshot"):
            continue
        name = label(node.get("name"), key)
        nodes[key] = {
            "id": key,
            "name": name,
            "type": node.get("resource_type"),
            "description": label(node.get("description"), ""),
            "depends_on": sorted(node.get("depends_on", {}).get("nodes", [])),
            "tags": sorted(node.get("tags", [])),
        }
        for parent in node.get("depends_on", {}).get("nodes", []):
            edges.append({"from": parent, "to": key})
    if len(nodes) > MAX_NODES:
        sys.exit(f"graph too large: {len(nodes)} nodes > {MAX_NODES}")
    if len(edges) > MAX_EDGES:
        sys.exit(f"graph too large: {len(edges)} edges > {MAX_EDGES}")
    # Depth check: longest dependency chain (bounded BFS over the edge list).
    children = {}
    for e in edges:
        children.setdefault(e["from"], []).append(e["to"])
    roots = [k for k in nodes if not any(e["to"] == k for e in edges)]
    depth = 0
    frontier = list(roots)
    seen = set()
    while frontier and depth <= MAX_DEPTH:
        depth += 1
        nxt = []
        for n in frontier:
            if n in seen:
                continue
            seen.add(n)
            nxt.extend(children.get(n, []))
        frontier = nxt
    if depth > MAX_DEPTH:
        sys.exit(f"graph too deep: depth {depth} > {MAX_DEPTH}")
    graph = {
        "schema": "public_graph/v1",
        "nodes": [nodes[k] for k in sorted(nodes)],
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"])),
        "counts": {"nodes": len(nodes), "edges": len(edges)},
    }
    with open(args.out, "w") as f:
        json.dump(graph, f, indent=2, sort_keys=True)
    print(f"public_graph.json: {len(nodes)} nodes, {len(edges)} edges")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""export_graph.py — manifest.json -> public_graph.json (allowlist only).

Reads the raw dbt manifest and emits the minimal public graph:
nodes (id, name, type, description, depends_on, tags) and edges
(parent -> child). Nothing else leaves the build plane: no manifest,
no catalog, no compiled SQL, no source file paths, no usernames,
no environment values, no row samples, no warehouse names.
Labels are emitted as plain text; consumers must encode them.
Enforces config/public-artifact-policy.yml limits.

Hardening (TASK-035):
- Topological cycle detection: a dependency cycle fails the export
  and the failure message names the cycle path.
- Depth is the true longest path over the projected graph, computed
  by memoised longest-path search, never by shortest visitation.
- Edges whose parent was omitted from the projection are dropped.
  The emitted graph never holds a dangling edge, and a node's
  emitted depends_on list holds projected parents only.
- Node strings are bounded, never silently truncated: a name or
  description over MAX_LABEL_CHARS, a tag over MAX_TAG_CHARS, or
  more than MAX_TAGS tags on one node fails the export.
"""
import argparse, json, sys

MAX_NODES = 500
MAX_EDGES = 2000
MAX_DEPTH = 10
MAX_LABEL_CHARS = 200
MAX_TAG_CHARS = 200
MAX_TAGS = 20
PROJECTED_TYPES = ("model", "seed", "test", "snapshot")

def fail(reason, detail):
    print(f"EXPORT FAILED: {reason}: {detail}", file=sys.stderr)
    sys.exit(1)

def checked_text(value, fallback, limit, reason, node_id):
    text = (value or fallback or "").strip()
    if len(text) > limit:
        fail(reason, f"node {node_id}: {len(text)} chars > limit {limit}")
    return text

def find_cycle(parents):
    """Return one cycle as a list of node IDs (first repeated at the
    end), or None. parents maps node ID -> projected parent IDs.
    Iterative DFS with an explicit path stack."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in parents}
    for start in sorted(parents):
        if color[start] != WHITE:
            continue
        stack = [(start, iter(sorted(parents[start])))]
        path = [start]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            advanced = False
            for nxt in it:
                if color[nxt] == GRAY:
                    idx = path.index(nxt)
                    return path[idx:] + [nxt]
                if color[nxt] == WHITE:
                    color[nxt] = GRAY
                    stack.append((nxt, iter(sorted(parents[nxt]))))
                    path.append(nxt)
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
                path.pop()
    return None

def longest_path_depth(parents):
    """Number of nodes on the longest dependency chain. Memoised
    longest-path search over the (now known acyclic) parent graph."""
    memo = {}
    def depth(node):
        if node in memo:
            return memo[node]
        ps = parents[node]
        memo[node] = 1 if not ps else 1 + max(depth(p) for p in ps)
        return memo[node]
    return max((depth(k) for k in parents), default=0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.manifest) as f:
        manifest = json.load(f)
    raw_nodes = manifest.get("nodes", {})
    projected = {k for k, n in raw_nodes.items()
                 if n.get("resource_type") in PROJECTED_TYPES}
    nodes = {}
    parents = {}
    dropped_edges = 0
    for key in sorted(projected):
        node = raw_nodes[key]
        name = checked_text(node.get("name"), key, MAX_LABEL_CHARS,
                            "OVERSIZED_NAME", key)
        description = checked_text(node.get("description"), "", MAX_LABEL_CHARS,
                                   "OVERSIZED_DESCRIPTION", key)
        tags = sorted(node.get("tags", []))
        if len(tags) > MAX_TAGS:
            fail("TOO_MANY_TAGS", f"node {key}: {len(tags)} tags > limit {MAX_TAGS}")
        for tag in tags:
            if len(tag) > MAX_TAG_CHARS:
                fail("OVERSIZED_TAG",
                     f"node {key}: tag of {len(tag)} chars > limit {MAX_TAG_CHARS}")
        declared = node.get("depends_on", {}).get("nodes", [])
        kept = sorted(p for p in declared if p in projected)
        dropped_edges += len(declared) - len(kept)
        parents[key] = kept
        nodes[key] = {
            "id": key,
            "name": name,
            "type": node.get("resource_type"),
            "description": description,
            "depends_on": kept,
            "tags": tags,
        }
    edges = [{"from": p, "to": k} for k in sorted(parents) for p in parents[k]]
    if len(nodes) > MAX_NODES:
        fail("GRAPH_TOO_LARGE", f"{len(nodes)} nodes > {MAX_NODES}")
    if len(edges) > MAX_EDGES:
        fail("GRAPH_TOO_LARGE", f"{len(edges)} edges > {MAX_EDGES}")
    cycle = find_cycle(parents)
    if cycle is not None:
        fail("CYCLE_DETECTED", " -> ".join(cycle))
    depth = longest_path_depth(parents)
    if depth > MAX_DEPTH:
        fail("DEPTH_EXCEEDED", f"longest path {depth} > {MAX_DEPTH}")
    graph = {
        "schema": "public_graph/v1",
        "nodes": [nodes[k] for k in sorted(nodes)],
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"])),
        "counts": {"nodes": len(nodes), "edges": len(edges)},
    }
    with open(args.out, "w") as f:
        json.dump(graph, f, indent=2, sort_keys=True)
    if dropped_edges:
        print(f"DANGLING_EDGE_DROPPED: {dropped_edges} edge(s) to omitted nodes dropped")
    print(f"public_graph.json: {len(nodes)} nodes, {len(edges)} edges")

if __name__ == "__main__":
    main()

# Architecture Overview Tool

`get_architecture_overview_tool` gives agents a compact architecture map after the graph has been built and post-processed. It is meant for orientation and architecture review, not for source-code reading.

## When to use it

Use `get_architecture_overview_tool` when:

- Starting work in an unfamiliar repository.
- Reviewing architecture at the community level.
- Looking for high-coupling areas.
- Choosing which community, file, flow, or dependency path to inspect next.

It is useful early in a session when an agent needs a bounded mental model before drilling into specific files, flows, callers, tests, or changed code.

## When not to use it

Do not use it when the task needs detailed source context. Prefer focused tools:

- `get_minimal_context_tool` for first-pass orientation.
- `detect_changes_tool` for changed-code review.
- `get_review_context_tool` for source snippets around changed code.
- `get_impact_radius_tool` for blast-radius analysis.
- `query_graph_tool` for callers, callees, importers, tests, and file summaries.
- `list_communities_tool(detail_level="minimal")` for a lightweight community list.
- `get_community_tool` for one community, optionally with member details.

## Output contract

The MCP tool returns a bounded structure:

- `status` - tool status.
- `summary` - human-readable count of communities, cross-community edges, and warnings.
- `communities` - bounded community metadata.
- `cross_community_edges` - capped examples of cross-community edges, or an empty list in minimal mode.
- `cross_community_edge_examples_included` - whether edge examples were included.
- `total_cross_community_edges` - full count of cross-community edges.
- `cross_community_edges_truncated` - whether edge examples were capped or intentionally omitted.
- `cross_community_coupling` - top coupling pairs with edge counts and edge kinds.
- `total_cross_community_coupling_pairs` - full count of coupling pairs.
- `cross_community_coupling_truncated` - whether coupling pairs were capped.
- `warnings` - high-coupling warnings, excluding test-dominated coupling.

Each returned community includes `member_count` instead of a full `members` list. Full member lists are available through focused community drill-downs.

## Detail levels

Use `detail_level="minimal"` for first-pass orientation. Minimal mode keeps communities, total counts, coupling summaries, and warnings, but omits verbose `cross_community_edges` examples.

Use `detail_level="standard"` when you need example source/target edges for follow-up graph exploration. Standard mode is the default and preserves backward-compatible behavior.

## Compact example

```json
{
  "status": "ok",
  "summary": "Architecture: 16 communities, 1157 cross-community edges, 2 warning(s)",
  "communities": [
    {
      "id": 1,
      "name": "tools",
      "member_count": 42,
      "cohesion": 0.71,
      "dominant_language": "python"
    },
    {
      "id": 2,
      "name": "graph",
      "member_count": 57,
      "cohesion": 0.68,
      "dominant_language": "python"
    }
  ],
  "cross_community_edges": [
    {
      "source_community": 1,
      "target_community": 2,
      "edge_kind": "CALLS",
      "source": "tools.py::run",
      "target": "graph.py::build"
    }
  ],
  "cross_community_edge_examples_included": true,
  "total_cross_community_edges": 1157,
  "cross_community_edges_truncated": true,
  "cross_community_coupling": [
    {
      "source_community": 1,
      "source_community_name": "tools",
      "target_community": 2,
      "target_community_name": "graph",
      "edge_count": 231,
      "edge_kinds": {"CALLS": 211, "REFERENCES": 20}
    }
  ],
  "total_cross_community_coupling_pairs": 3,
  "cross_community_coupling_truncated": false,
  "warnings": []
}
```

In this example, `source_community: 1` points to the community object with `id: 1` and `name: "tools"`. `target_community: 2` points to the community object with `id: 2` and `name: "graph"`. These IDs are community identifiers from the graph, not ranks or priorities, and they can vary between repositories or graph rebuilds.

## Why the output must stay bounded

MCP clients often store a tool result more than once, usually as both text content and structured content. Large payloads can therefore be multiplied inside an agent session.

A real large-repository issue showed the failure mode:

- Old JSON result size: `1,528,862` chars.
- Largest community: `4,864` members, `644,438` JSON chars by itself.
- Session record size after MCP/client duplication: `4,598,692` chars.
- Estimated wasted context: roughly `250k` to `300k` tokens for one tool call.

The root cause was returning every `communities[].members` list in the global architecture overview. That detail belongs in targeted community inspection, not in a global overview.

## Bounded behavior

The overview uses bounded output by design:

- Full community member lists are used internally for calculations but are not returned.
- Each returned community has `member_count` instead of `members`.
- Cross-community edge examples are capped.
- Total counts and truncation flags preserve accuracy.
- Coupling pairs are summarized with counts and edge-kind breakdowns.

Measured on a large repository:

- Before: `1,528,862` JSON chars.
- After: `31,890` JSON chars.
- Reduction: `97.91%`.

## Large repository safety

For agent workflows on large repositories:

1. Start with `get_minimal_context_tool`.
2. Use `get_architecture_overview_tool(detail_level="minimal")` for community-level orientation.
3. Use `list_communities_tool(detail_level="minimal")` when you only need names, sizes, and cohesion.
4. Use `get_community_tool()` for bounded community metadata and a small member-name sample.
5. Use `get_community_tool(include_member_names=true)` only when the full member-name list is needed.
6. Use `get_community_tool(include_members=true)` only after choosing one specific community and needing full member node details.
7. Use `query_graph_tool(detail_level="minimal")` or `detect_changes_tool(detail_level="minimal")` when a compact result is enough.
8. Avoid embedding full real payloads in issues, logs, docs, or handoffs.

## Operational note

If an agent launches code-review-graph with `uvx code-review-graph serve`, local checkout changes do not affect the active MCP server until the package is installed from the fixed checkout, the package is published and upgraded, or the MCP config is pointed at the local checkout. Restart the agent or MCP server after changing the installed source.

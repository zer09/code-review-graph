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

The MCP tool wrapper returns a bounded structure:

- `status` - tool status (`ok` or `error`).
- `summary` - human-readable count of communities, non-`TESTED_BY` cross-community edges, and warnings.
- `communities` - bounded community metadata. Each item includes `id`, `name`, `level`, `cohesion`, `size`, `member_count`, `dominant_language`, and `description`; it intentionally omits `members`.
- `cross_community_edges` - capped examples of non-`TESTED_BY` cross-community edges in standard mode, or an empty list in minimal mode. `source` and `target` are sanitized and truncated graph qualified names.
- `cross_community_edge_examples_included` - whether edge examples were included.
- `total_cross_community_edges` - full count of non-`TESTED_BY` cross-community edges.
- `cross_community_edges_truncated` - whether edge examples were capped or intentionally omitted.
- `cross_community_coupling` - top non-`TESTED_BY` community pairs with edge counts and edge-kind breakdowns. The pair IDs are sorted to de-duplicate opposite directions; they are not directional source and target IDs.
- `total_cross_community_coupling_pairs` - full count of coupling pairs.
- `cross_community_coupling_truncated` - whether coupling pairs were capped.
- `warnings` - high-coupling warnings for pairs above the threshold. `TESTED_BY` edges are ignored, and warnings are filtered with a name-based test-community heuristic. Coupling summaries still include non-`TESTED_BY` pairs involving test-like communities, and generated test names not matched by the heuristic may still warn.
- `_hints` - follow-up tool suggestions and warning hints added by the MCP tool wrapper.

The lower-level `get_architecture_overview` helper returns the overview keys without wrapper fields such as `status`, `summary`, and `_hints`. Full member lists are available through focused community drill-downs.

## Detail levels

Use `detail_level="minimal"` for first-pass orientation. Minimal mode keeps communities, total counts, truncation flags, coupling summaries, warnings, status, summary, and hints, but sets `cross_community_edges` to an empty list and `cross_community_edge_examples_included` to `false`.

Use `detail_level="standard"` when you need example source/target edges for follow-up graph exploration. Standard mode is the default and includes up to 100 edge examples.

Unknown detail levels default to standard mode.

## Compact example

```json
{
  "status": "ok",
  "summary": "Architecture: 2 communities, 128 cross-community edges, 1 warning(s)",
  "communities": [
    {
      "id": 1,
      "name": "tools",
      "level": 0,
      "cohesion": 0.71,
      "size": 42,
      "member_count": 42,
      "dominant_language": "python",
      "description": "Directory-based community: tools"
    },
    {
      "id": 2,
      "name": "graph",
      "level": 0,
      "cohesion": 0.68,
      "size": 57,
      "member_count": 57,
      "dominant_language": "python",
      "description": "Directory-based community: graph"
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
  "total_cross_community_edges": 128,
  "cross_community_edges_truncated": true,
  "cross_community_coupling": [
    {
      "source_community": 1,
      "source_community_name": "tools",
      "target_community": 2,
      "target_community_name": "graph",
      "edge_count": 128,
      "edge_kinds": {"CALLS": 108, "REFERENCES": 20}
    }
  ],
  "total_cross_community_coupling_pairs": 1,
  "cross_community_coupling_truncated": false,
  "warnings": [
    "High coupling (128 edges) between 'tools' and 'graph'"
  ],
  "_hints": {
    "next_steps": [
      {"tool": "list_communities", "suggestion": "Drill into individual communities"},
      {"tool": "detect_changes", "suggestion": "See how recent changes affect the architecture"},
      {"tool": "list_flows", "suggestion": "Explore execution flows"}
    ],
    "related": [],
    "warnings": [
      "High coupling (128 edges) between 'tools' and 'graph'"
    ]
  }
}
```

In this example, `source_community: 1` in an edge example points to the community object with `id: 1` and `name: "tools"`; `target_community: 2` points to the community object with `id: 2` and `name: "graph"`. In `cross_community_coupling`, the pair IDs are sorted for aggregation and should be read as a community pair, not as call direction. These IDs are community identifiers from the graph, not ranks or priorities, and they can vary between repositories or graph rebuilds.

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
- Standard mode caps cross-community edge examples at 100.
- Coupling pair summaries are capped at 50.
- `TESTED_BY` edges are excluded from cross-community edge counts, examples, coupling summaries, and warnings.
- Total counts and truncation flags preserve accuracy for non-`TESTED_BY` cross-community edges.
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

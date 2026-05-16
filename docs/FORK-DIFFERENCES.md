# Fork Differences from Upstream

Audience: maintainers and AI agents that need to distinguish this fork from `upstream/main` and safely merge future upstream updates.

## Baseline

| Field | Value |
|---|---|
| Upstream remote | `git@github.com:tirth8205/code-review-graph.git` |
| Fork remote | `git@github.com:zer09/code-review-graph.git` |
| Baseline upstream ref | `upstream/main` |
| Baseline commit at time of writing | `52cf3bc63ee77c8b204fb809791a5f212e83a2de` |
| Fork branch checked | `main` |
| Fork commit at time of writing | `52cf3bc63ee77c8b204fb809791a5f212e83a2de` |
| Important status note | At time of writing, `origin/main`, `upstream/main`, and `HEAD` point to the same commit. The fork delta described here is in the working tree until committed. |

Update this table after each successful upstream merge or after committing new fork-only behavior.

## Quick identification rules for AI agents

This checkout contains fork-only behavior if any of these are true:

1. `get_architecture_overview_tool` accepts `detail_level`.
2. `get_architecture_overview_tool(detail_level="minimal")` returns no edge examples but preserves totals and coupling summaries.
3. Architecture overview communities contain `member_count` and do not contain full `members` lists.
4. `get_community_tool` accepts `include_member_names` and `members_sample_limit`.
5. `get_community_tool()` returns bounded metadata with `member_count`, `members_sample`, and `members_truncated` by default.
6. `docs/ARCHITECTURE-OVERVIEW.md` and this file exist.
7. `tests/test_docs_hardening.py` exists and checks MCP tool documentation against source defaults.

If none of these are true, assume the checkout behaves like upstream for the areas described here.

## Fork-only behavior map

### 1. Architecture overview payload hardening

Source files:

- `code_review_graph/communities.py`
- `code_review_graph/tools/community_tools.py`
- `code_review_graph/main.py`

MCP-facing behavior:

```text
get_architecture_overview_tool(repo_root=null, detail_level="standard")
```

Fork additions relative to upstream:

- Adds `detail_level` to architecture overview.
- Keeps `detail_level="standard"` as the default for backward compatibility.
- Adds `detail_level="minimal"` for agent-safe first-pass architecture orientation.
- Removes full `communities[].members` from the global overview response.
- Returns `member_count` in each community summary instead of full member lists.
- Caps standard-mode cross-community edge examples at 100.
- Caps cross-community coupling summaries at 50 pairs.
- Adds metadata that lets agents know whether examples were included or truncated.

Important output fields added by the fork:

```text
cross_community_edge_examples_included
total_cross_community_edges
cross_community_edges_truncated
cross_community_coupling
total_cross_community_coupling_pairs
cross_community_coupling_truncated
```

Behavior contract:

| Mode | Edge examples | Totals | Coupling summaries | Warnings | Intended use |
|---|---:|---:|---:|---:|---|
| `standard` | Up to 100 | Yes | Yes | Yes | Backward-compatible detailed overview |
| `minimal` | 0 | Yes | Yes | Yes | Token-efficient agent orientation |

Merge risk:

- High if upstream changes community detection, architecture overview output, or MCP schema generation.
- Check this area carefully when merging upstream changes to `code_review_graph/communities.py`, `code_review_graph/tools/community_tools.py`, or `code_review_graph/main.py`.

### 2. Community detail payload hardening

Source files:

- `code_review_graph/tools/community_tools.py`
- `code_review_graph/main.py`

MCP-facing behavior:

```text
get_community_tool(
  community_name=null,
  community_id=null,
  include_members=false,
  include_member_names=false,
  members_sample_limit=20,
  repo_root=null,
)
```

Fork additions relative to upstream:

- Adds `include_member_names`.
- Adds `members_sample_limit`.
- Makes bounded metadata the default response.
- Returns `member_count`, `members_sample`, and `members_truncated` by default.
- Full member names require `include_member_names=true`.
- Full member node details require `include_members=true`.

Default response contract:

```text
community.id
community.name
community.level
community.cohesion
community.size
community.member_count
community.dominant_language
community.description
community.members_sample
community.members_truncated
```

Fields intentionally absent by default:

```text
community.members
community.member_details
```

Merge risk:

- Medium to high if upstream changes community detail responses or MCP parameter names.
- Preserve bounded defaults unless there is an explicit decision to trade token safety for compatibility.

### 3. Agent-facing documentation and discoverability

Source and docs files:

- `code_review_graph/tools/docs.py`
- `docs/ARCHITECTURE-OVERVIEW.md`
- `docs/COMMANDS.md`
- `docs/LLM-OPTIMIZED-REFERENCE.md`
- `docs/FEATURES.md`
- `docs/INDEX.md`
- `docs/TROUBLESHOOTING.md`
- `docs/USAGE.md`

Fork additions relative to upstream:

- Adds a dedicated architecture overview contract document.
- Adds this fork-differences document and exposes it through `get_docs_section_tool(section_name="fork-differences")`.
- Adds compact MCP signatures for all 30 MCP tools in `docs/LLM-OPTIMIZED-REFERENCE.md`.
- Documents `detail_level="minimal"` as the preferred agent-safe mode where supported.
- Documents community drill-down safety and opt-ins.
- Documents architecture overview token-safety behavior.
- Corrects documentation for `apply_refactor_tool(dry_run=false)`.

Important distinction:

- `apply_refactor_tool.dry_run` is not fork-only behavior. Upstream source already defaults it to `False` at the baseline commit. The fork only corrects and hardens the docs around that default.
- `build_or_update_graph_tool.base="HEAD~1"` is not fork-only behavior. It is upstream and fork behavior at the baseline commit.

### 4. Documentation hardening tests

Test file:

- `tests/test_docs_hardening.py`

Fork additions relative to upstream:

- Validates that Markdown docs do not use unresolved task markers.
- Validates internal docs links.
- Validates docs do not contain adversarial prompt-injection strings.
- Validates docs do not include known unsafe large-payload patterns.
- Validates `docs/COMMANDS.md` MCP tool names and parameter sets against `code_review_graph/main.py`.
- Validates `docs/LLM-OPTIMIZED-REFERENCE.md` compact signatures and defaults against source defaults.

Merge risk:

- Medium. If upstream adds, removes, or renames MCP tools, these tests should fail until docs are updated.
- Treat those failures as useful merge guards, not flaky tests.

### 5. Test and dependency changes

Files:

- `tests/test_communities.py`
- `tests/test_tools.py`
- `pyproject.toml`
- `uv.lock`

Fork additions relative to upstream:

- Adds tests for architecture overview standard and minimal modes.
- Adds tests for bounded community detail payloads.
- Adds tests for `include_member_names` behavior.
- Adds docs hardening test coverage.
- Adds `pytest-asyncio` to the dev dependency group so async pytest tests run without plugin warnings or failures.

Current validation expectation:

```text
env -u CRG_RECURSE_SUBMODULES uv run pytest -q
```

Expected result at time of writing:

```text
1246 passed, 1 skipped, 2 xpassed
```

Expected skip:

```text
tests/test_communities.py:116 - igraph not installed
```

Expected xpasses:

```text
tests/test_notebook.py::TestRKernelNotebook::test_r_kernel_detects_functions
tests/test_notebook.py::TestRKernelNotebook::test_r_kernel_detects_imports
```

### 6. Investigation and validation artifacts

Files:

- `docs/ARCHITECTURE-OVERVIEW-TOKEN-EFFICIENCY-PLAN.md`
- `docs/COMMUNITY-TOOL-HARDENING-PLAN.md`
- `docs/HARDENING-PLAN.md`
- `docs/ROUND3-REVIEW-FOLLOWUP-IMPLEMENTATION-PLAN.md`
- `docs/findings/round1test.md`
- `docs/findings/round2test.md`
- `docs/findings/round3test.md`
- `docs/findings/round4test.md`
- `docs/findings/round5test.md`
- `docs/findings/round6test.md`
- `docs/findings/final-mcp-smoke-test.md`

Purpose:

- Preserve why the fork changed architecture overview and community payload behavior.
- Preserve MCP smoke-test evidence.
- Preserve issue-investigation context for future upstream merges.

Merge risk:

- Low for runtime behavior.
- Medium for docs maintenance, because these files may become stale if behavior changes.

## Upstream merge playbook

Use this when upstream publishes new commits.

### 1. Refresh refs

```bash
git fetch upstream --prune
git fetch origin --prune
```

### 2. Confirm baseline before merging

```bash
git status --short
git rev-parse HEAD
git rev-parse upstream/main
git merge-base HEAD upstream/main
git rev-list --left-right --count upstream/main...HEAD
```

If the working tree is dirty, commit or stash fork work before merging.

### 3. Merge upstream

Prefer a merge commit over rebasing shared fork history:

```bash
git merge upstream/main
```

Resolve conflicts with these priorities:

1. Preserve upstream bug fixes and parser improvements.
2. Preserve fork payload-safety contracts documented in this file.
3. Preserve MCP schema backward compatibility where possible.
4. Update docs and tests in the same merge commit when behavior changes.

### 4. Conflict hotspots

Review these files carefully after every upstream merge:

```text
code_review_graph/communities.py
code_review_graph/tools/community_tools.py
code_review_graph/main.py
code_review_graph/tools/docs.py
docs/COMMANDS.md
docs/LLM-OPTIMIZED-REFERENCE.md
docs/ARCHITECTURE-OVERVIEW.md
tests/test_communities.py
tests/test_tools.py
tests/test_docs_hardening.py
pyproject.toml
uv.lock
```

### 5. Post-merge validation

Run at minimum:

```bash
env -u CRG_RECURSE_SUBMODULES uv run pytest -q
env -u CRG_RECURSE_SUBMODULES uv run ruff check tests/test_docs_hardening.py docs/COMMANDS.md docs/LLM-OPTIMIZED-REFERENCE.md
```

Then verify live MCP schema and docs alignment:

```text
MCP tool count: 30, unless upstream intentionally changed it.
docs/COMMANDS.md tool count matches MCP schema.
docs/LLM-OPTIMIZED-REFERENCE.md compact signatures match MCP schema.
get_docs_section_tool(section_name="commands") includes all MCP tools and options.
```

For payload safety, run a large-repository smoke test if available:

```text
get_architecture_overview_tool(detail_level="minimal")
get_architecture_overview_tool(detail_level="standard")
get_community_tool(include_members=false, members_sample_limit=5)
```

Expected safety properties:

```text
minimal architecture overview has zero cross_community_edges examples.
minimal and standard preserve the same total_cross_community_edges.
standard architecture overview returns at most 100 cross_community_edges examples.
community detail default has no full members and no member_details.
community detail default has member_count, members_sample, and members_truncated.
```

### 6. Update this document

After each upstream merge:

1. Update the baseline commit table.
2. Add any new fork-only behavior.
3. Remove entries that upstream has adopted.
4. Update conflict hotspots if files moved.
5. Update validation results.

## Upstream adoption checklist

If upstream later implements similar features, do not keep duplicate fork code blindly. Compare behavior against this contract:

- Does upstream expose `detail_level` on `get_architecture_overview_tool`?
- Does upstream omit full `communities[].members` from architecture overview?
- Does upstream preserve `total_cross_community_edges` when examples are omitted?
- Does upstream cap edge examples and coupling summaries?
- Does upstream provide bounded `get_community_tool()` defaults?
- Does upstream expose full member names and full member details only through explicit opt-ins?
- Do upstream docs expose all MCP tools and defaults accurately?

If upstream behavior matches or improves the fork contract, prefer upstream implementation and delete fork-only duplicate code.

## Machine-readable summary

```yaml
fork_name: zer09/code-review-graph
upstream_name: tirth8205/code-review-graph
baseline_commit: 52cf3bc63ee77c8b204fb809791a5f212e83a2de
fork_delta_state_at_writing: working_tree_uncommitted
fork_only_features:
  architecture_overview_token_safety:
    files:
      - code_review_graph/communities.py
      - code_review_graph/tools/community_tools.py
      - code_review_graph/main.py
    mcp_tool: get_architecture_overview_tool
    parameters_added:
      - detail_level
    response_fields_added:
      - cross_community_edge_examples_included
      - total_cross_community_edges
      - cross_community_edges_truncated
      - cross_community_coupling
      - total_cross_community_coupling_pairs
      - cross_community_coupling_truncated
    limits:
      standard_edge_examples: 100
      coupling_pairs: 50
  community_detail_token_safety:
    files:
      - code_review_graph/tools/community_tools.py
      - code_review_graph/main.py
    mcp_tool: get_community_tool
    parameters_added:
      - include_member_names
      - members_sample_limit
    default_response_added:
      - member_count
      - members_sample
      - members_truncated
    default_response_removed:
      - members
      - member_details
  docs_discoverability:
    files:
      - code_review_graph/tools/docs.py
      - docs/ARCHITECTURE-OVERVIEW.md
      - docs/COMMANDS.md
      - docs/LLM-OPTIMIZED-REFERENCE.md
      - docs/FORK-DIFFERENCES.md
  docs_hardening_tests:
    files:
      - tests/test_docs_hardening.py
not_fork_only:
  - apply_refactor_tool.dry_run_false_default
  - build_or_update_graph_tool.base_HEAD_tilde_1_default
validation_command: env -u CRG_RECURSE_SUBMODULES uv run pytest -q
last_known_validation: 1246 passed, 1 skipped, 2 xpassed
```

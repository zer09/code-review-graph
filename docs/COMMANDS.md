# All Available Commands

This page is the human-readable command and MCP surface reference. Verify it against `code_review_graph/main.py` and `code-review-graph --help` when adding or removing tools.

## Skills (Claude Code slash commands)

### `/code-review-graph:build-graph`
Build or update the knowledge graph.
- First time: performs a full build
- Subsequent runs: incremental update, parsing only changed files

### `/code-review-graph:review-delta`
Review only changes since the last commit.
- Auto-detects changed files via git diff
- Computes blast radius, with depth 2 by default
- Generates structured review guidance

### `/code-review-graph:review-pr`
Review a PR or branch diff.
- Uses main or master as base
- Runs impact analysis across all PR commits
- Produces structured output with risk assessment

## MCP Tools (30 total)

### Recommended entry point

#### `get_minimal_context_tool`
```
task: str = ""                    # What you are doing
changed_files: list[str] | None    # Auto-detected if omitted
repo_root: str | None              # Auto-detected if omitted
base: str = "HEAD~1"              # Git diff base
```
Always call this first for orientation. It returns graph stats, risk, top communities/flows, and suggested next tools in a compact response.

### Build and graph health tools

#### `build_or_update_graph_tool`
```
full_rebuild: bool = False         # True for full re-parse
repo_root: str | None              # Auto-detected if omitted
base: str = "HEAD~1"              # Git diff base for incremental updates
postprocess: str = "full"         # full, minimal, or none
recurse_submodules: bool | None    # Falls back to CRG_RECURSE_SUBMODULES when None
```

#### `run_postprocess_tool`
```
flows: bool = True                 # Run flow detection
communities: bool = True           # Run community detection
fts: bool = True                   # Rebuild FTS index
repo_root: str | None              # Auto-detected if omitted
```
Use this after a build with `postprocess="none"` or `postprocess="minimal"`, or to rerun expensive post-processing independently.

#### `list_graph_stats_tool`
```
repo_root: str | None
```

### Query and review tools

#### `get_impact_radius_tool`
```
changed_files: list[str] | None    # Auto-detected from git if omitted
max_depth: int = 2                 # Hops in graph
repo_root: str | None
base: str = "HEAD~1"
detail_level: str = "standard"    # standard or minimal
```

#### `query_graph_tool`
```
pattern: str                       # callers_of, callees_of, imports_of,
                                   # importers_of, children_of, tests_for,
                                   # inheritors_of, file_summary
target: str                        # Node name, qualified name, or file path
repo_root: str | None
detail_level: str = "standard"    # standard or minimal
```

#### `get_review_context_tool`
```
changed_files: list[str] | None
max_depth: int = 2
include_source: bool = True
max_lines_per_file: int = 200
repo_root: str | None
base: str = "HEAD~1"
detail_level: str = "standard"    # standard or minimal
```

#### `detect_changes_tool`
```
base: str = "HEAD~1"
changed_files: list[str] | None
include_source: bool = False
max_depth: int = 2
repo_root: str | None
detail_level: str = "standard"    # standard or minimal
```
Primary tool for code review. Maps git diffs to affected functions, flows, communities, and test coverage gaps. Returns risk scores and prioritized review items.

#### `semantic_search_nodes_tool`
```
query: str                         # Search string
kind: str | None                   # File, Class, Function, Type, Test
limit: int = 20
repo_root: str | None
model: str | None                  # Embedding model
provider: str | None               # Embedding provider
detail_level: str = "standard"    # standard or minimal
```

#### `find_large_functions_tool`
```
min_lines: int = 50                # Minimum line count threshold
kind: str | None                   # File, Class, Function, or Test
file_path_pattern: str | None      # Filter by file path substring
limit: int = 50                    # Max results to return
repo_root: str | None
```

#### `traverse_graph_tool`
```
query: str                         # Search string for the starting node
mode: str = "bfs"                 # bfs or dfs
depth: int = 3                     # Max traversal depth, 1-6
token_budget: int = 2000           # Approximate result budget
repo_root: str | None
```

### Documentation and embedding tools

#### `embed_graph_tool`
```
repo_root: str | None
model: str | None                  # Embedding model name
provider: str | None               # Embedding provider
```
Requires: `pip install code-review-graph[embeddings]`

#### `get_docs_section_tool`
```
section_name: str                  # usage, review-delta, review-pr, commands,
                                   # architecture-overview, fork-differences,
                                   # legal, watch, embeddings, languages,
                                   # troubleshooting
repo_root: str | None
```

### Flow tools

#### `list_flows_tool`
```
sort_by: str = "criticality"      # criticality, depth, node_count, file_count, name
limit: int = 50
kind: str | None                   # Filter by entry point kind, e.g. Test or Function
detail_level: str = "standard"    # standard or minimal
repo_root: str | None
```

#### `get_flow_tool`
```
flow_id: int | None                # Database ID from list_flows_tool
flow_name: str | None              # Name to search, partial match
include_source: bool = False       # Include source snippets for each step
repo_root: str | None
```

#### `get_affected_flows_tool`
```
changed_files: list[str] | None    # Auto-detected from git if omitted
base: str = "HEAD~1"
repo_root: str | None
```

### Community tools

#### `list_communities_tool`
```
sort_by: str = "size"             # size, cohesion, name
min_size: int = 0
detail_level: str = "standard"    # standard or minimal
repo_root: str | None
```
Use `detail_level="minimal"` for initial orientation on large repositories.

#### `get_community_tool`
```
community_name: str | None         # Name to search, partial match
community_id: int | None           # Database ID
include_members: bool = False      # Include full member node details
include_member_names: bool = False # Include full member qualified-name list
members_sample_limit: int = 20     # Bounded member-name preview size
repo_root: str | None
```
By default this returns `member_count`, a bounded `members_sample`, and `members_truncated`; it does not return the full `members` list. Use `include_member_names=True` only when full member names are needed. Use `include_members=True` only for focused drill-downs into one community.

#### `get_architecture_overview_tool`
```
repo_root: str | None
detail_level: str = "standard"    # standard includes edge examples; minimal omits them
```
Generates a bounded high-level architecture map from detected communities and cross-community coupling. Use `detail_level="minimal"` for first-pass orientation and `detail_level="standard"` when edge examples are useful.

Returns community metadata with `member_count`, optional capped cross-community edge examples, total counts, truncation flags, coupling summaries, and warnings. It intentionally does not return full community member lists because large repositories can otherwise produce multi-megabyte MCP payloads.

See [ARCHITECTURE-OVERVIEW.md](ARCHITECTURE-OVERVIEW.md) for output shape and token-safety details.

### Graph analysis tools

#### `get_hub_nodes_tool`
```
top_n: int = 10
repo_root: str | None
```
Finds the most connected nodes in the codebase. These are architectural hotspots with high blast radius.

#### `get_bridge_nodes_tool`
```
top_n: int = 10
repo_root: str | None
```
Finds architectural chokepoints using betweenness centrality.

#### `get_knowledge_gaps_tool`
```
repo_root: str | None
```
Identifies isolated nodes, thin communities, untested hotspots, and single-file communities.

#### `get_surprising_connections_tool`
```
top_n: int = 15
repo_root: str | None
```
Finds unexpected architectural coupling, including cross-community, cross-language, peripheral-to-hub, and cross-test-boundary edges.

#### `get_suggested_questions_tool`
```
repo_root: str | None
```
Generates prioritized review questions from graph analysis.

### Refactoring tools

#### `refactor_tool`
```
mode: str = "rename"              # rename, dead_code, or suggest
old_name: str | None               # Current symbol name for rename
new_name: str | None               # New symbol name for rename
kind: str | None                   # Function or Class for dead_code
file_pattern: str | None           # Filter by file path substring
repo_root: str | None
```

#### `apply_refactor_tool`
```
refactor_id: str                   # ID from prior refactor_tool call
repo_root: str | None
dry_run: bool = False              # Preview changes without writing files
```

### Wiki tools

#### `generate_wiki_tool`
```
repo_root: str | None
force: bool = False                # Regenerate all pages even if unchanged
```

#### `get_wiki_page_tool`
```
community_name: str                # Community name to look up
repo_root: str | None
```

### Multi-repo tools

#### `list_repos_tool`
```
(no parameters)
```

#### `cross_repo_search_tool`
```
query: str
kind: str | None
limit: int = 20
```

## MCP Prompts (5 workflow templates)

### `review_changes`
Pre-commit review workflow using detect_changes, affected_flows, and test gaps.
```
base: str = "HEAD~1"
```

### `architecture_map`
Architecture documentation using communities, flows, and Mermaid diagrams.

### `debug_issue`
Guided debugging using search, flow tracing, and recent changes.
```
description: str = ""
```

### `onboard_developer`
New developer orientation using stats, architecture, and critical flows.

### `pre_merge_check`
PR readiness check with risk scoring, test gaps, and dead code detection.
```
base: str = "HEAD~1"
```

## CLI Commands

```bash
# Setup
code-review-graph install           # Register MCP server with supported AI coding platforms
code-review-graph install --dry-run # Preview without writing files
code-review-graph init              # Alias for install

# Build and update
code-review-graph build                        # Full build
code-review-graph build --skip-flows           # Skip flow/community detection
code-review-graph build --skip-postprocess     # Raw parse only
code-review-graph update                       # Incremental update
code-review-graph update --base origin/main    # Custom base ref
code-review-graph postprocess                  # Re-run flows, communities, and FTS
code-review-graph postprocess --no-flows       # Skip flow detection

# Monitor and inspect
code-review-graph status                       # Graph statistics
code-review-graph watch                        # Auto-update on file changes
code-review-graph visualize                    # Generate interactive HTML graph

# Analysis
code-review-graph detect-changes               # Risk-scored change analysis
code-review-graph detect-changes --base HEAD~3 # Custom base ref
code-review-graph detect-changes --brief       # Compact output

# Wiki
code-review-graph wiki                         # Generate markdown wiki from communities

# Multi-repo
code-review-graph register <path> [--alias name]  # Register a repository
code-review-graph unregister <path_or_alias>       # Remove from registry
code-review-graph repos                            # List registered repositories

# Daemon, included with install and no extra dependencies
code-review-graph daemon start [--foreground]       # Start the watch daemon
code-review-graph daemon stop                       # Stop the daemon
code-review-graph daemon restart [--foreground]     # Restart the daemon
code-review-graph daemon status                     # Show daemon status and repos
code-review-graph daemon logs [--repo ALIAS] [-f]   # View daemon or per-repo logs
code-review-graph daemon add <path> [--alias NAME]  # Add a repo to daemon config
code-review-graph daemon remove <path_or_alias>     # Remove a repo from daemon config

# Evaluation
code-review-graph eval                         # Run evaluation benchmarks

# Server
code-review-graph serve                        # Start MCP server over stdio
code-review-graph serve --http                 # Start MCP server over Streamable HTTP
code-review-graph mcp                          # Alias for serve
```

## Standalone Daemon CLI (`crg-daemon`)

The `crg-daemon` command is included with every `code-review-graph` installation. It is also available as a standalone entry point. It mirrors the `code-review-graph daemon` subcommands:

```bash
crg-daemon start [--foreground]       # Start the multi-repo watch daemon
crg-daemon stop                       # Stop the daemon and all watcher processes
crg-daemon restart [--foreground]     # Restart: stop, then start
crg-daemon status                     # Show daemon status, repos, and process liveness
crg-daemon logs [--repo ALIAS] [-f] [-n N]  # Tail daemon or per-repo log files
crg-daemon add <path> [--alias NAME]  # Add a repository to watch.toml
crg-daemon remove <path_or_alias>     # Remove a repository from watch.toml
```

### Configuration

The daemon reads its configuration from `~/.code-review-graph/watch.toml`:

```toml
session_name = "crg-watch"   # logical daemon name
log_dir = "~/.code-review-graph/logs"
poll_interval = 2            # seconds between config file polls

[[repos]]
path = "/path/to/project-a"
alias = "project-a"

[[repos]]
path = "/path/to/project-b"
alias = "project-b"
```

The daemon spawns one `code-review-graph watch` child process per repo, managed via `subprocess.Popen`. It monitors the config file for changes and automatically reconciles child processes as repos are added or removed. Health checks run every 30 seconds and automatically restart dead watchers. No external dependencies such as tmux or screen are required.

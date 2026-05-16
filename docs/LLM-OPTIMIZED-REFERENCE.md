# LLM-OPTIMIZED REFERENCE -- code-review-graph v2.3.3

Claude Code: read only the exact `<section>` you need. Never load the whole file.

<section name="usage">
Quick install: pip install code-review-graph
Then: code-review-graph install && code-review-graph build
First run: /code-review-graph:build-graph
After that use only delta/pr commands.
Always start with get_minimal_context_tool(task="your task"). It returns compact risk, communities, flows, and suggested next tools.
Use detail_level="minimal" where the tool supports it unless you need more detail.
</section>

<section name="review-delta">
1. Call get_minimal_context_tool(task="review changes") first.
2. If risk is low: detect_changes_tool(detail_level="minimal") -> report summary.
3. If risk is medium or high: detect_changes_tool(detail_level="standard") -> expand on high-risk items.
Target: <=5 tool calls and <=800 tokens total context.
</section>

<section name="review-pr">
Fetch PR diff -> detect_changes_tool -> get_affected_flows_tool -> structured review with blast-radius table and risk scores.
Never include full files unless explicitly asked.
</section>

<section name="commands">
MCP tools (30) compact signatures:
- build_or_update_graph_tool(full_rebuild=false, repo_root=null, base="HEAD~1", postprocess="full", recurse_submodules=null)
- run_postprocess_tool(flows=true, communities=true, fts=true, repo_root=null)
- get_minimal_context_tool(task="", changed_files=null, repo_root=null, base="HEAD~1")
- get_impact_radius_tool(changed_files=null, max_depth=2, repo_root=null, base="HEAD~1", detail_level="standard")
- query_graph_tool(pattern, target, repo_root=null, detail_level="standard")
- get_review_context_tool(changed_files=null, max_depth=2, include_source=true, max_lines_per_file=200, repo_root=null, base="HEAD~1", detail_level="standard")
- semantic_search_nodes_tool(query, kind=null, limit=20, repo_root=null, model=null, provider=null, detail_level="standard")
- embed_graph_tool(repo_root=null, model=null, provider=null)
- list_graph_stats_tool(repo_root=null)
- get_docs_section_tool(section_name, repo_root=null)
- find_large_functions_tool(min_lines=50, kind=null, file_path_pattern=null, limit=50, repo_root=null)
- list_flows_tool(sort_by="criticality", limit=50, kind=null, detail_level="standard", repo_root=null)
- get_flow_tool(flow_id=null, flow_name=null, include_source=false, repo_root=null)
- get_affected_flows_tool(changed_files=null, base="HEAD~1", repo_root=null)
- list_communities_tool(sort_by="size", min_size=0, detail_level="standard", repo_root=null)
- get_community_tool(community_name=null, community_id=null, include_members=false, include_member_names=false, members_sample_limit=20, repo_root=null)
- get_architecture_overview_tool(repo_root=null, detail_level="standard")
- detect_changes_tool(base="HEAD~1", changed_files=null, include_source=false, max_depth=2, repo_root=null, detail_level="standard")
- refactor_tool(mode="rename", old_name=null, new_name=null, kind=null, file_pattern=null, repo_root=null)
- apply_refactor_tool(refactor_id, repo_root=null, dry_run=false)
- generate_wiki_tool(repo_root=null, force=false)
- get_wiki_page_tool(community_name, repo_root=null)
- get_hub_nodes_tool(top_n=10, repo_root=null)
- get_bridge_nodes_tool(top_n=10, repo_root=null)
- get_knowledge_gaps_tool(repo_root=null)
- get_surprising_connections_tool(top_n=15, repo_root=null)
- get_suggested_questions_tool(repo_root=null)
- traverse_graph_tool(query, mode="bfs", depth=3, token_budget=2000, repo_root=null)
- list_repos_tool()
- cross_repo_search_tool(query, kind=null, limit=20)
MCP prompts (5): review_changes, architecture_map, debug_issue, onboard_developer, pre_merge_check
Skills: build-graph, review-delta, review-pr
CLI: code-review-graph [install|init|build|update|postprocess|watch|status|visualize|serve|mcp|wiki|detect-changes|register|unregister|repos|daemon|eval]
Token efficiency: call get_minimal_context_tool first. Use detail_level="minimal" for supported tools. For architecture overview, minimal omits edge examples while preserving totals and coupling. For communities, use list_communities_tool(detail_level="minimal") before get_community_tool(). Use include_member_names=true or include_members=true only for focused drill-downs.
</section>

<section name="architecture-overview">
get_architecture_overview_tool(detail_level="minimal") returns bounded community-level architecture data without edge examples.
Communities include member_count, not full members.
cross_community_edges is an empty list in minimal mode and capped in standard mode; totals remain in total_cross_community_edges plus cross_community_edges_truncated.
get_community_tool() is bounded by default with member_count and members_sample. Use include_member_names=true for full names or include_members=true for full node details only after selecting one community.
Use docs/ARCHITECTURE-OVERVIEW.md for the full payload contract.
</section>

<section name="fork-differences">
This fork is zer09/code-review-graph. Upstream is tirth8205/code-review-graph. Baseline at writing: upstream/main 52cf3bc63ee77c8b204fb809791a5f212e83a2de.
Fork-only behavior: architecture overview token safety, get_community_tool bounded defaults, include_member_names, members_sample_limit, detail_level on get_architecture_overview_tool, schema-checked command docs, and docs hardening tests.
Not fork-only: apply_refactor_tool dry_run=false and build_or_update_graph_tool base="HEAD~1" already exist upstream at the baseline.
Use docs/FORK-DIFFERENCES.md before merging upstream updates.
</section>

<section name="legal">
MIT license. 100% local. No telemetry. DB file: .code-review-graph/graph.db
</section>

<section name="watch">
Run: code-review-graph watch (auto-updates graph on file save via watchdog)
Or use PostToolUse hooks for automatic background updates.
</section>

<section name="embeddings">
Optional: pip install code-review-graph[embeddings]
Then call embed_graph_tool to compute vectors.
semantic_search_nodes_tool auto-uses vectors when available, falls back to keyword plus FTS5.
Providers: Local (all-MiniLM-L6-v2, 384-dim), Google Gemini, MiniMax (embo-01, 1536-dim).
Configure via CRG_EMBEDDING_MODEL env var, model parameter, or provider parameter.
</section>

<section name="languages">
Supported: Python, TypeScript/TSX, JavaScript, Vue, Go, Rust, Java, Scala, C#, Ruby, Kotlin, Swift, PHP, Solidity, C/C++, Dart, R, Perl, Lua, and additional Tree-sitter language-pack parsers when available.
Parser: Tree-sitter via tree-sitter-language-pack
</section>

<section name="troubleshooting">
DB lock: SQLite WAL mode, auto-recovers. Only one build at a time.
Large repos: First build 30-60s. Incremental <2s. Add patterns to .code-review-graphignore.
Large MCP payload: start with get_minimal_context_tool, use detail_level="minimal", and drill down with focused tools.
Stale graph: Run /code-review-graph:build-graph manually.
Missing nodes: Check language support and ignore patterns. Use full_rebuild=True.
Windows/WSL: Use forward slashes in paths. Ensure uv is on PATH in WSL.
</section>

**Instruction to Claude Code (always follow):**
When user asks anything about "code-review-graph", "how to use", "commands", "review-delta", etc.:
1. Call get_docs_section_tool with the exact section name.
2. Use only that content plus current graph state.
3. Never include full docs or source code in your reasoning.
This guarantees 90%+ token savings.

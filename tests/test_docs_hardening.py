"""Documentation hardening checks."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

DECORATIVE_UNICODE = "\u2013\u2014\u2026\u2018\u2019\u201c\u201d\u2192\u2264\u2265"
HOME_PATH_RE = re.compile(r"(/home/[^\s`)]+|/Users/[^\s`)]+|C:\\\\Users\\\\)")
TASK_MARKER_RE = re.compile(r"\b(TODO|FIXME|XXX|TBD)\b", re.IGNORECASE)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def _docs() -> list[Path]:
    return sorted(DOCS_DIR.glob("*.md"))


def _lines_outside_fences(path: Path):
    in_fence = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line_no, line


def _slug(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.strip().lower())
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"\s+", "-", text).strip("-")


def test_docs_have_single_h1() -> None:
    failures: list[str] = []
    for path in _docs():
        h1s = [line_no for line_no, line in _lines_outside_fences(path) if line.startswith("# ")]
        if len(h1s) != 1:
            failures.append(f"{path.relative_to(ROOT)} has {len(h1s)} H1 headings: {h1s}")

    assert not failures, "\n".join(failures)


def test_docs_are_copy_paste_safe() -> None:
    failures: list[str] = []
    for path in _docs():
        for line_no, line in _lines_outside_fences(path):
            if any(ch in line for ch in DECORATIVE_UNICODE):
                failures.append(
                    f"{path.relative_to(ROOT)}:{line_no}: decorative Unicode punctuation"
                )
            if HOME_PATH_RE.search(line):
                failures.append(f"{path.relative_to(ROOT)}:{line_no}: user-specific home path")
            if TASK_MARKER_RE.search(line):
                failures.append(f"{path.relative_to(ROOT)}:{line_no}: unresolved task marker")

    assert not failures, "\n".join(failures)


def test_docs_internal_links_resolve() -> None:
    failures: list[str] = []
    for path in _docs():
        text = path.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = raw.strip().split()[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not str(dest).startswith(str(ROOT.resolve())):
                failures.append(f"{path.relative_to(ROOT)}: link escapes repo: {raw}")
                continue
            if file_part and not dest.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing link target: {raw}")
                continue
            if anchor:
                headings = {
                    _slug(line.lstrip("#"))
                    for _, line in _lines_outside_fences(dest)
                    if re.match(r"^#{1,6}\s+", line)
                }
                if anchor.lower() not in headings:
                    failures.append(f"{path.relative_to(ROOT)}: missing anchor: {raw}")

    assert not failures, "\n".join(failures)


def _default_to_doc(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _actual_tool_defaults(main_text: str) -> dict[str, dict[str, str]]:
    tree = ast.parse(main_text)
    result: dict[str, dict[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.endswith("_tool"):
            continue
        args = [arg.arg for arg in node.args.args if arg.arg != "self"]
        defaults = ["<required>"] * (len(args) - len(node.args.defaults))
        defaults.extend(
            _default_to_doc(ast.literal_eval(default))
            for default in node.args.defaults
        )
        result[node.name] = dict(zip(args, defaults, strict=True))
    return result


def _actual_tool_params(main_text: str) -> dict[str, set[str]]:
    return {
        tool: set(params)
        for tool, params in _actual_tool_defaults(main_text).items()
    }


def _documented_tool_params(command_text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    headings = list(re.finditer(r"^#### `([^`]+_tool)`", command_text, re.MULTILINE))
    for index, heading in enumerate(headings):
        name = heading.group(1)
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(command_text)
        body = command_text[start:end]
        code_block = re.search(r"```\s*\n(.*?)\n```", body, re.DOTALL)
        params: set[str] = set()
        if code_block:
            for line in code_block.group(1).splitlines():
                match = re.match(r"\s*([A-Za-z_]\w*)\s*(?::|=)", line)
                if match:
                    params.add(match.group(1))
        result[name] = params
    return result


def _split_signature_params(signature: str) -> list[str]:
    params: list[str] = []
    current = ""
    in_quote = False
    for char in signature:
        if char == '"':
            in_quote = not in_quote
            current += char
        elif char == "," and not in_quote:
            params.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        params.append(current.strip())
    return params


def _llm_tool_defaults(llm_text: str) -> dict[str, dict[str, str]]:
    section = re.search(
        r'<section name="commands">(.*?)</section>',
        llm_text,
        re.DOTALL | re.IGNORECASE,
    )
    assert section is not None
    result: dict[str, dict[str, str]] = {}
    for line in section.group(1).splitlines():
        match = re.match(r"-\s+([A-Za-z_]\w*_tool)\((.*)\)", line.strip())
        if not match:
            continue
        params: dict[str, str] = {}
        signature = match.group(2).strip()
        if signature:
            for raw_param in _split_signature_params(signature):
                name, sep, default = raw_param.partition("=")
                params[name.strip()] = default.strip().strip('"') if sep else "<required>"
        result[match.group(1)] = params
    return result


def test_command_docs_match_mcp_tool_wrappers() -> None:
    command_text = (DOCS_DIR / "COMMANDS.md").read_text(encoding="utf-8")
    main_text = (ROOT / "code_review_graph" / "main.py").read_text(encoding="utf-8")
    llm_text = (DOCS_DIR / "LLM-OPTIMIZED-REFERENCE.md").read_text(encoding="utf-8")

    documented_params = _documented_tool_params(command_text)
    actual_defaults = _actual_tool_defaults(main_text)
    actual_params = {
        tool: set(params)
        for tool, params in actual_defaults.items()
    }
    llm_defaults = _llm_tool_defaults(llm_text)
    documented = set(documented_params)
    actual = set(actual_params)

    assert documented == actual
    assert documented_params == actual_params
    assert llm_defaults == actual_defaults

    header = re.search(r"## MCP Tools \((\d+) total\)", command_text)
    assert header is not None
    assert int(header.group(1)) == len(actual)

    llm_header = re.search(r"MCP tools \((\d+)\)", llm_text)
    assert llm_header is not None
    assert int(llm_header.group(1)) == len(actual)
    missing_from_llm = sorted(tool for tool in actual if tool not in llm_text)
    assert missing_from_llm == []

    missing_params_from_llm = sorted(
        f"{tool}.{param}"
        for tool, params in actual_params.items()
        for param in params
        if param not in llm_text
    )
    assert missing_params_from_llm == []
    assert "include_member_names" in command_text
    assert "members_sample_limit" in command_text
    assert "detail_level: str = \"standard\"" in command_text


def test_llm_reference_version_matches_project_version() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    first_line = (DOCS_DIR / "LLM-OPTIMIZED-REFERENCE.md").read_text(
        encoding="utf-8"
    ).splitlines()[0]

    assert f"v{version}" in first_line

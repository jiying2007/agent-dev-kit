"""Harness readiness checks for MCP tools, permissions, and secret boundaries."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .readiness_evidence import (
    SECRET_REFERENCE,
    RepositoryIndex,
    _blocker,
    _deduplicate,
    _material_evidence,
)
from .strict_json import StrictJSONError, loads as load_strict_json


def _walk_json(value: Any, parts: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            item = value[key]
            current = parts + (str(key),)
            yield current, str(key), item
            yield from _walk_json(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_json(item, parts + (str(index),))


def _safe_secret_reference(value: str) -> bool:
    stripped = value.strip()
    if stripped.lower().startswith("basic "):
        return bool(SECRET_REFERENCE.fullmatch(stripped[6:].strip()))
    return not stripped or bool(SECRET_REFERENCE.fullmatch(stripped))


def _sensitive_key(key: str, fragments: Sequence[str]) -> bool:
    camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    normalized = re.sub(r"[^a-z0-9]", "_", camel.lower()).strip("_")
    compact = normalized.replace("_", "")
    for fragment in (*fragments, "auth", "credential", "credentials"):
        token = re.sub(r"[^a-z0-9]", "_", fragment.lower()).strip("_")
        if (normalized == token or normalized.endswith("_" + token)
                or compact == token.replace("_", "")
                or compact.endswith(token.replace("_", ""))
                or ("_" + token + "_") in ("_" + normalized + "_")):
            return True
    return False



_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?=(?<![A-Za-z0-9_-])(--?[A-Za-z][A-Za-z0-9_-]*|[A-Za-z][A-Za-z0-9_-]*)\s*([=:])\s*([^\s;,&]+))",
    re.IGNORECASE,
)
_CREDENTIAL_INLINE = re.compile(
    r"(?:^|[\s;])--?([A-Za-z][A-Za-z0-9_-]*)\s+([^\s;,&]+)", re.IGNORECASE,
)
_AUTH_SCHEME = re.compile(r"\b(?:Bearer|Basic)\s+([^\s;,&]+)", re.IGNORECASE)
_EMPTY_CREDENTIAL = re.compile(
    r"(?<![A-Za-z0-9_-])(--?[A-Za-z][A-Za-z0-9_-]*)\s*[=:]\s*(?=$|[;,&])",
    re.IGNORECASE,
)
_CREDENTIAL_FLAG = re.compile(r"--?([A-Za-z][A-Za-z0-9_-]*)\Z")


def _literal_credential_argument(text: str, fragments: Sequence[str]) -> bool:
    """Guard shell-like credential literals without evaluating shell or echoing input."""
    # A zero-width scan also sees nested assignments (e.g. --env=TOKEN=value)
    # rather than consuming the complete argument at --env=.
    for match in _CREDENTIAL_ASSIGNMENT.finditer(text):
        name = match.group(1).lstrip("-")
        if not _sensitive_key(name, fragments):
            continue
        if name.lower() == "authorization":
            candidate = text[match.end(2):].strip().split(";", 1)[0].strip()
        else:
            candidate = match.group(3)
        if not candidate or not _safe_secret_reference(candidate):
            return True
    for match in _CREDENTIAL_INLINE.finditer(text):
        if _sensitive_key(match.group(1), fragments) and not _safe_secret_reference(match.group(2)):
            return True
    for match in _AUTH_SCHEME.finditer(text):
        if not _safe_secret_reference(match.group(1)):
            return True
    return False


def _credential_argument_issues(
    server: Mapping[str, Any], fragments: Sequence[str],
) -> Tuple[List[str], bool]:
    """Return opaque argument locations and malformed-input status, never values."""
    args = server.get("args", [])
    if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
        return [], True
    issues: List[str] = []
    malformed = False
    command = server.get("command")
    if isinstance(command, str):
        if _literal_credential_argument(command, fragments):
            issues.append("command")
        if any(_sensitive_key(match.group(1).lstrip("-"), fragments)
               for match in _EMPTY_CREDENTIAL.finditer(command)):
            malformed = True
    for position, value in enumerate(args):
        if _literal_credential_argument(value, fragments):
            issues.append("args[{}]".format(position))
        if any(_sensitive_key(match.group(1).lstrip("-"), fragments)
               for match in _EMPTY_CREDENTIAL.finditer(value)):
            malformed = True
        flag = _CREDENTIAL_FLAG.fullmatch(value)
        if flag and _sensitive_key(flag.group(1), fragments):
            if position + 1 >= len(args) or not args[position + 1] or args[position + 1].startswith("-"):
                malformed = True
            elif not _safe_secret_reference(args[position + 1]):
                issues.append("args[{}]".format(position + 1))
    return sorted(set(issues)), malformed



_URL_SINK_NAMES = frozenset(("url", "uri", "endpoint", "baseurl", "serverurl", "sseurl"))
_SECURITY_OBJECT_NAMES = frozenset(("env", "headers", "httpheaders", "requestheaders"))


def _mcp_url_key(key: str) -> bool:
    return re.sub(r"[^a-z0-9]", "", key.lower()) in _URL_SINK_NAMES


def _url_credential_issues(value: Any, fragments: Sequence[str]) -> Tuple[bool, bool]:
    """Return (literal-credential, malformed) without returning or logging URL text."""
    if not isinstance(value, str) or not value.strip() or len(value) > 8192 or value.count("&") > 128:
        return False, True
    try:
        parts = urlsplit(value)
        if (parts.scheme.lower() not in ("http", "https", "ws", "wss")
                or not parts.netloc or not parts.hostname
                or any(char.isspace() or char == "\\\\" for char in parts.netloc)):
            return False, True
        # Accessing .port raises ValueError for malformed and out-of-range ports.
        port = parts.port
        if port == 0:
            return False, True
        query = parse_qsl(parts.query, keep_blank_values=True, errors="strict",
                          max_num_fields=129)
        if "=" in parts.fragment:
            query += parse_qsl(parts.fragment, keep_blank_values=True, errors="strict",
                               max_num_fields=129)
        username = parts.username
        password = parts.password
        # A literal password is unconditionally a credential violation,
        # even if the username has another malformed or non-managed value.
        if password is not None:
            password = unquote(password, errors="strict")
            if not _safe_secret_reference(password):
                return True, False
        if username is not None:
            username = unquote(username, errors="strict")
            if _literal_credential_argument(username, fragments):
                return True, False
            # Username may itself be an authentication identity. Only
            # verifiable managed references may be embedded in source URLs.
            if not _safe_secret_reference(username):
                return False, True
        if (password is not None) != (username is not None):
            return False, True
    except (ValueError, UnicodeError):
        return False, True
    for key, content in query:
        if ((_sensitive_key(key, fragments) and not _safe_secret_reference(content))
                or _literal_credential_argument(content, fragments)):
            return True, False
    return False, False


def _opaque_sensitive_ref(
    relative: str, parts: Tuple[str, ...], positions: Mapping[str, int], ordinal: int,
) -> str:
    """No arbitrary server names or JSON keys may occur in a blocker ref."""
    if len(parts) >= 2 and parts[0] == "mcpServers" and parts[1] in positions:
        return "{}#mcpServers[{}].sensitive[{}]".format(relative, positions[parts[1]], ordinal)
    return "{}#sensitive[{}]".format(relative, ordinal)


def _unpinned_npx_dependency(server: Mapping[str, Any]) -> Optional[str]:
    command = server.get("command")
    args = server.get("args")
    if not isinstance(command, str) or Path(command).name not in {"npx", "pnpx", "bunx"}:
        return None
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        return "args"
    candidates = [item for item in args if item and not item.startswith("-")]
    if not candidates:
        return "args"
    package = candidates[0]
    if (
        package.startswith(("/", "./", "../"))
        or re.match(r"^[A-Za-z]:[\\/]", package)
        or package.endswith((".js", ".mjs", ".cjs"))
    ):
        return None
    if package.startswith("@"):
        separator = package.rfind("@")
        if separator <= 0:
            return package
        version = package[separator + 1 :]
    elif "@" in package:
        version = package.rsplit("@", 1)[1]
    else:
        return package
    return None if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version) else package


def _positive_permission_term(content: str, term: str) -> bool:
    lowered = content.lower()
    expected = term.lower()
    for match in re.finditer(re.escape(expected), lowered):
        prefix = lowered[max(0, match.start() - 48) : match.start()]
        window = lowered[max(0, match.start() - 48) : min(len(lowered), match.end() + 32)]
        if re.search(r"(?:\bnot\b|\bno\b|\bwithout\b|\bnever\b).{0,32}$", prefix):
            continue
        if re.search(r"(?:不|无|未|禁止|不得).{0,16}$", prefix):
            continue
        if re.search(r"hardcod(?:e|es|ed|ing).{0,24}(?:credential|secret|token|password)", window):
            continue
        return True
    return False


def _permission_document_evidence(index: RepositoryIndex, contract: Mapping[str, Any]) -> List[str]:
    candidates: List[str] = []
    for relative in sorted(index.files):
        lowered = relative.lower()
        if not _material_evidence(relative):
            continue
        if relative == "AGENTS.md" or (
            relative.startswith("docs/") and any(token in lowered for token in ("mcp", "permission", "security", "tool"))
        ):
            candidates.append(relative)
    groups = contract["mcp"]["permission_evidence_terms"]
    matched: List[str] = []
    found_groups = set()
    for relative in candidates[: int(contract["mcp"]["max_permission_docs"])]:
        content = index.read_text(relative)
        if content is None:
            continue
        lowered = content.lower()
        for name, terms in groups.items():
            if any(_positive_permission_term(lowered, str(term)) for term in terms):
                found_groups.add(name)
                matched.append(relative)
    return _deduplicate(matched, 12) if len(found_groups) == len(groups) else []


def _structured_permission_evidence(
    metadata: Mapping[str, Any], contract: Mapping[str, Any]
) -> Tuple[str, List[str], List[Dict[str, str]]]:
    metadata_path = str(contract["metadata_path"])
    dimensions = metadata.get("dimensions", {})
    raw = dimensions.get("tool_and_permission_boundary", {}) if isinstance(dimensions, dict) else {}
    policy = contract["mcp"]["structured_permission_boundary"]
    boundary = raw.get(policy["metadata_key"]) if isinstance(raw, dict) else None
    if boundary is None:
        return "missing", [], [
            _blocker(
                "missing_structured_permission_boundary",
                "MCP 存在但 readiness metadata 未声明结构化权限边界",
                metadata_path,
            )
        ]
    if not isinstance(boundary, dict):
        return "invalid", [metadata_path], [
            _blocker(
                "invalid_structured_permission_boundary",
                "结构化权限边界必须是对象",
                metadata_path,
            )
        ]
    required_true = policy["required_true_fields"]
    source_field = policy["credential_source_field"]
    allowed_sources = set(policy["allowed_credential_sources"])
    if any(boundary.get(field) is not True for field in required_true) or boundary.get(
        source_field
    ) not in allowed_sources:
        return "invalid", [metadata_path], [
            _blocker(
                "invalid_structured_permission_boundary",
                "结构化权限边界必须明确只读、审批和受支持的凭证来源",
                metadata_path,
            )
        ]
    return "pass", [metadata_path], []


def _evaluate_tools(
    index: RepositoryIndex,
    contract: Mapping[str, Any],
    metadata: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, str]]]:
    names = set(str(item).lower() for item in contract["mcp"]["config_names"])
    all_configs = sorted(
        relative
        for relative in index.files
        if _material_evidence(relative) and Path(relative).name.lower() in names
    )
    unsafe_configs = sorted(
        relative for relative in index.unsafe_mcp_configs if _material_evidence(relative)
    )
    if (not all_configs and not unsafe_configs
            and not index.unsafe_mcp_config_overflow):
        return "not-applicable", [], []
    blockers: List[Dict[str, str]] = []
    blocker_limit = int(contract["scan"]["max_blockers_per_dimension"])
    omitted_blockers = 0

    def record_blocker(item: Dict[str, str]) -> None:
        nonlocal omitted_blockers
        if len(blockers) < blocker_limit - 1:
            blockers.append(item)
        else:
            omitted_blockers += 1

    def bounded_blockers() -> List[Dict[str, str]]:
        if omitted_blockers:
            return blockers + [
                _blocker("blockers_truncated", "另有 {} 个 MCP blocker 未展开".format(omitted_blockers))
            ]
        return list(blockers)

    parse_failed = bool(unsafe_configs) or index.unsafe_mcp_config_overflow
    for position, relative in enumerate(unsafe_configs):
        record_blocker(
            _blocker(
                "unsafe_mcp_config",
                "发现符号链接、目录或非普通文件形式的 MCP 配置，无法安全读取",
                "{}#unsafe[{}]".format(Path(relative).name.lower(), position),
            )
        )
    if index.unsafe_mcp_config_overflow:
        record_blocker(_blocker("mcp_config_limit_exceeded", "不安全 MCP 配置超过扫描预算"))
    hardcoded_secret = False
    unpinned = False
    max_configs = int(contract["mcp"]["max_configs"])
    configs = all_configs[:max_configs]
    if len(all_configs) > max_configs:
        parse_failed = True
        record_blocker(
            _blocker(
                "mcp_config_limit_exceeded",
                "MCP 配置数量 {} 超过扫描上限 {}".format(len(all_configs), max_configs),
            )
        )
    fragments = [str(item) for item in contract["mcp"]["sensitive_key_fragments"]]
    for relative in configs:
        content = index.read_text(relative)
        if content is None:
            parse_failed = True
            record_blocker(_blocker("unreadable_mcp_config", "MCP 配置无法在扫描预算内读取", relative))
            continue
        try:
            data = load_strict_json(content, max_bytes=index.max_file_bytes)
        except StrictJSONError:
            parse_failed = True
            record_blocker(_blocker("invalid_mcp_json", "MCP 配置不是有效 JSON", relative))
            continue
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
            parse_failed = True
            record_blocker(_blocker("invalid_mcp_schema", "MCP 配置必须包含 mcpServers 对象", relative))
            continue
        servers = data["mcpServers"]
        server_positions = {name: position for position, name in enumerate(sorted(servers))}
        sensitive_ordinal = 0
        for parts, key, value in _walk_json(data):
            source = _opaque_sensitive_ref(relative, parts, server_positions, sensitive_ordinal)
            key_folded = key.lower()
            if (key_folded in _SECURITY_OBJECT_NAMES
                    and (not isinstance(value, dict)
                         or any(not isinstance(item, str) for item in value.values()))):
                parse_failed = True
                record_blocker(
                    _blocker("invalid_mcp_security_fields", "MCP env/headers 必须是字符串映射", source)
                )
                sensitive_ordinal += 1
                continue
            url_literal, url_invalid = (
                _url_credential_issues(value, fragments)
                if _mcp_url_key(key) else (False, False)
            )
            if url_invalid:
                parse_failed = True
                record_blocker(
                    _blocker("invalid_mcp_url", "MCP URL 类型、编码或预算不符合输入契约", source)
                )
                sensitive_ordinal += 1
                continue
            if value is None:
                continue
            header_literal = (
                isinstance(value, str)
                and any(part.lower() in ("headers", "httpheaders", "requestheaders")
                        for part in parts[:-1])
                and _literal_credential_argument(value, fragments)
            )
            env_literal = (
                isinstance(value, str)
                and "env" in (part.lower() for part in parts[:-1])
                and _literal_credential_argument(value, fragments)
            )
            if not (_sensitive_key(key, fragments) or header_literal
                    or env_literal or url_literal):
                continue
            if (header_literal or env_literal or url_literal or not isinstance(value, str)
                    or not _safe_secret_reference(value)):
                hardcoded_secret = True
                record_blocker(
                    _blocker(
                        "hardcoded_mcp_secret",
                        "MCP 配置含非环境引用的敏感值；值已脱敏",
                        source,
                    )
                )
                sensitive_ordinal += 1
        for server_name, position in server_positions.items():
            server = servers[server_name]
            opaque = "{}#mcpServers[{}]".format(relative, position)
            if not isinstance(server, dict):
                parse_failed = True
                record_blocker(_blocker("invalid_mcp_server", "MCP server 定义必须是对象", opaque))
                continue
            if ("command" in server
                    and (not isinstance(server["command"], str) or not server["command"].strip())):
                parse_failed = True
                record_blocker(
                    _blocker("invalid_mcp_command", "MCP command 必须是非空字符串", opaque + ".command")
                )
            if "command" not in server and not any(_mcp_url_key(key) for key in server):
                parse_failed = True
                record_blocker(
                    _blocker("invalid_mcp_server_endpoint", "MCP 缺少 command 或 URL 声明", opaque)
                )
            unsafe, malformed = _credential_argument_issues(server, fragments)
            if malformed:
                parse_failed = True
                record_blocker(_blocker("invalid_mcp_command_args", "MCP 凭证参数不完整或类型无效", opaque + ".args"))
            for location in unsafe:
                hardcoded_secret = True
                record_blocker(
                    _blocker(
                        "hardcoded_mcp_secret",
                        "MCP command/args 含明文凭证；值已脱敏",
                        opaque + "." + location,
                    )
                )
            if _unpinned_npx_dependency(server) is not None:
                unpinned = True
                record_blocker(
                    _blocker("unpinned_mcp_dependency", "npx 类 MCP dependency 未固定版本", opaque + ".args")
                )
    permission_refs = _permission_document_evidence(index, contract)
    structured_status, structured_refs, structured_blockers = _structured_permission_evidence(
        metadata or {}, contract
    )
    evidence = configs + structured_refs + permission_refs
    if hardcoded_secret:
        return "blocked", evidence, bounded_blockers()
    if parse_failed or unpinned:
        return "needs-review", evidence, bounded_blockers()
    for blocker in structured_blockers:
        record_blocker(blocker)
    if structured_status == "invalid":
        return "needs-review", evidence, bounded_blockers()
    if structured_status == "missing":
        return "partial", evidence, bounded_blockers()
    if not permission_refs:
        record_blocker(_blocker("missing_permission_boundary", "MCP 存在但未发现只读、审批和凭证边界证据"))
        return "partial", evidence, bounded_blockers()
    return "pass", evidence, bounded_blockers()

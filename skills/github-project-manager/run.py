#!/usr/bin/env python3
"""Prepare a minimal, auditable latest-source snapshot. Never uploads to GitHub."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from collections import Counter

VERSION = "1.0.0"
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:[-_].*)?$", re.I)
SKIP_DIRS = {
    ".git", ".svn", ".hg", ".idea", ".vscode", ".claude", ".codex",
    ".pytest_cache", ".mypy_cache", "__pycache__", "node_modules",
    ".venv", "venv", "cache", ".cache", "output", "verification",
    "dist", "build", ".tmp", "tmp", "logs", "log", "data", "backups",
    "backup", "coverage", "artifacts", ".next", ".nuxt", "target",
}
EXCLUDED_SUFFIXES = (
    ".exe", ".dll", ".so", ".dylib", ".bin", ".db", ".sqlite", ".sqlite3",
    ".log", ".pyc", ".zip", ".7z", ".tar", ".gz", ".tgz", ".pfx",
    ".pem", ".key", ".p12", ".p8", ".mmdb", ".node", ".wasm", ".map",
    ".tsbuildinfo", ".bak", ".sqlite-wal", ".sqlite-shm",
)
TEXT_SUFFIXES = {
    ".go", ".mod", ".sum", ".sql", ".py", ".js", ".jsx", ".ts",
    ".tsx", ".vue", ".mjs", ".cjs", ".mts", ".cts", ".css", ".html",
    ".json", ".jsonc", ".yml", ".yaml", ".toml", ".xml", ".lua",
    ".conf", ".sh", ".ps1", ".cmd", ".bat", ".service", ".example",
    ".md", ".txt", ".scss", ".less", ".svelte", ".rs", ".lock",
    ".php", ".rb", ".java", ".kt", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".fs", ".proto", ".tf",
}
ASSET_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff", ".woff2"}
ROOT_SPECIAL = {
    ".gitignore", "Makefile", "Dockerfile", "Containerfile",
    "go.mod", "go.sum", "Cargo.lock", "Cargo.toml",
    "package.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock", "requirements.txt", "Pipfile.lock",
    "pyproject.toml", "poetry.lock", "CMakeLists.txt",
}
CREDENTIAL_FILE_RE = re.compile(
    r"(?i)(^\.env($|\.)|(^|[._ -])(password|passwords|credential|credentials|"
    r"masterkey|privatekey|secret|secrets|token)([._ -]|$))"
)
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "token_pattern": re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{25,}|github_pat_[A-Za-z0-9_]{30,}|"
                                r"AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9_-]{25,})"),
    "credential_url": re.compile(r"(?i)[?&](?:key|token|api_key|password|secret|pkey)=[A-Za-z0-9_.-]{14,}"),
}
CONFIG_LITERAL_RE = re.compile(
    r"(?im)^\s*(?:[A-Z0-9_]*(?:SECRET|PASSWORD|ACCESS_TOKEN|API_KEY|MASTER_KEY|PRIVATE_KEY))"
    r"\s*:\s*['\"]([^'\"\r\n]{10,})['\"]\s*(?:#.*)?$"
)


def err(code, message):
    return {"ok": False, "code": code, "message": message}


def within(child, root):
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_version(project):
    if VERSION_RE.fullmatch(project.name):
        return project.parent, project, project.name
    versions = []
    for item in project.iterdir():
        if not item.is_dir() or item.is_symlink():
            continue
        match = VERSION_RE.fullmatch(item.name)
        if match:
            versions.append((tuple(map(int, match.groups())), item.name, item))
    if versions:
        versions.sort()
        latest = versions[-1][2]
        return project, latest, latest.name
    return project, project, None


def excluded_file(file):
    low = file.name.lower()
    if low in {".env", "auth.json", "credentials.json", "id_rsa", "id_ed25519"}:
        return True
    if CREDENTIAL_FILE_RE.search(file.name) and file.suffix.lower() not in TEXT_SUFFIXES:
        return True
    if any(low.endswith(ext) for ext in EXCLUDED_SUFFIXES):
        return True
    if low.endswith(("-wal", "-shm")):
        return True
    return False


def source_allowed(relative):
    parts = relative.parts
    name = relative.name
    if excluded_file(relative):
        return False
    if name in ROOT_SPECIAL or name.startswith("Dockerfile.") or name.startswith("Containerfile."):
        return True
    if relative.suffix.lower() in ASSET_SUFFIXES:
        return any(part in {"static", "assets", "src", "public", "testdata", "webdist"} for part in parts[:-1])
    if relative.suffix.lower() == ".md":
        if len(parts) == 1:
            return name in {"AGENTS.md", "README.md", "REQUEST_GUARD.md"} or name.endswith("_CONTRACT.md") or name.endswith("_GUIDE.md")
        return "docs" in parts or "deploy" in parts or "deployment" in parts
    if relative.suffix.lower() == ".txt":
        return name.lower() in {"requirements.txt"} or "testdata" in parts
    return relative.suffix.lower() in TEXT_SUFFIXES


def walk_selected(folder):
    selected = []
    for current, dirs, files in os.walk(folder, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                         and not d.startswith(".") and not (current_path / d).is_symlink())
        for name in sorted(files):
            f = current_path / name
            if f.is_symlink() or not f.is_file():
                continue
            relative = f.relative_to(folder)
            if source_allowed(relative):
                selected.append(f)
    return selected


def document_candidates(project, latest_label):
    options = []
    for base in [project, project / "docs", project / "docs" / "plan"]:
        if not base.is_dir():
            continue
        for f in base.glob("*.md"):
            if not f.is_file() or f.is_symlink():
                continue
            name = f.name
            if latest_label and (latest_label in name or "交接" in name or "handoff" in name.lower()):
                options.append((f.stat().st_mtime, f.relative_to(project).as_posix()))
    return [name for _, name in sorted(options, reverse=True)[:25]]


def collect(project, extra_docs):
    project, chosen, label = resolve_version(project)
    selected = {f.relative_to(chosen): f for f in walk_selected(chosen)}
    # Under a versioned project, keep relative location of original source files.
    if chosen != project:
        selected = {Path(chosen.name) / rel: f for rel, f in selected.items()}
    # The project-level instructions and current handoff are helpful across versions.
    for name in ("AGENTS.md", "项目交接文档.md"):
        f = project / name
        if f.is_file() and not f.is_symlink():
            selected[Path(name)] = f
    if chosen == project:
        pass
    for raw in extra_docs:
        if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
            raise ValueError("include_docs must contain relative project paths")
        f = (project / raw).resolve()
        if not within(f, project) or not f.is_file() or f.is_symlink():
            raise ValueError("include_docs path not in project or not a regular file")
        if f.suffix.lower() != ".md":
            raise ValueError("include_docs permits Markdown files only")
        selected[f.relative_to(project)] = f
    return project, chosen, label, selected


def scan_file(f, name):
    if f.suffix.lower() in ASSET_SUFFIXES:
        return []
    try:
        content = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [{"path": name, "kind": "non_utf8", "line": None}]
    found = []
    for kind, pattern in SECRET_PATTERNS.items():
        matches = list(pattern.finditer(content))
        for match in matches[:15]:
            found.append({"path": name, "kind": kind, "line": content.count("\n", 0, match.start()) + 1})
    if f.suffix.lower() in {".yml", ".yaml", ".json", ".example", ".toml", ".conf"} or f.name.startswith("Dockerfile"):
        for match in list(CONFIG_LITERAL_RE.finditer(content))[:15]:
            val = match.group(1)
            if not any(x in val.lower() for x in ("example", "replace", "placeholder", "change_me", "changeme")):
                found.append({"path": name, "kind": "literal_config_secret", "line": content.count("\n", 0, match.start()) + 1})
    return found


def inventory(project, extra_docs):
    project, chosen, label, files = collect(project, extra_docs)
    findings = []
    for path, f in files.items():
        findings.extend(scan_file(f, path.as_posix()))
    counter = Counter(path.parts[0] if len(path.parts) > 1 else "root" for path in files)
    total = sum(f.stat().st_size for f in files.values())
    info = {
        "project_dir": str(project),
        "source_dir": str(chosen),
        "version": label or "unversioned",
        "file_count": len(files),
        "source_bytes": total,
        "by_directory": dict(counter),
        "suggested_docs": document_candidates(project, label),
        "findings": findings,
        "ready_for_upload_review": not findings,
    }
    return info, files


def main(request):
    action = request.get("skill_action")
    if action == "status":
        return {"ok": True, "name": "github-project-manager", "version": VERSION,
                "actions": ["status", "inspect", "prepare"], "network_operations": False}
    if action not in ("inspect", "prepare"):
        return err("UNKNOWN_ACTION", "Expected status, inspect or prepare.")
    raw = request.get("project_dir")
    if not isinstance(raw, str) or not raw.strip():
        return err("PROJECT_REQUIRED", "project_dir must be a non-empty absolute path.")
    project = Path(raw).expanduser().resolve()
    if not project.is_dir():
        return err("PROJECT_NOT_FOUND", "project_dir must name an existing directory.")
    extra = request.get("include_docs", [])
    if not isinstance(extra, list) or not all(isinstance(v, str) for v in extra):
        return err("DOC_PATHS_INVALID", "include_docs must be an array of relative Markdown paths.")
    try:
        info, files = inventory(project, extra)
    except ValueError as e:
        return err('DOC_PATHS_INVALID', str(e))
    if action == "inspect":
        return {"ok": True, **info}
    target_raw = request.get("output_dir")
    if not isinstance(target_raw, str) or not target_raw.strip():
        return err("OUTPUT_REQUIRED", "prepare requires an unused output_dir.")
    target = Path(target_raw).expanduser().resolve()
    if within(target, project) or within(project, target):
        return err("OUTPUT_OVERLAPS_PROJECT", "Temporary output directory must be separate from source.")
    if target.exists():
        return err("OUTPUT_EXISTS", "output_dir must not exist; no automatic overwrite.")
    target.mkdir(parents=True, exist_ok=False)
    manifest = []
    for rel, original in sorted(files.items()):
        output = target / rel
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, output)
        raw = original.read_bytes()
        if hashlib.sha256(output.read_bytes()).digest() != hashlib.sha256(raw).digest():
            raise RuntimeError("Staged copy does not match original: " + rel.as_posix())
        manifest.append({"path": rel.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    report = {**info, "manifest": manifest, "original_files_unmodified": True}
    (target / "source-manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, **info, "staging_dir": str(target),
            "manifest_file": str(target / "source-manifest.json"),
            "note": "Do not commit source-manifest.json. Review findings before publishing."}


def run():
    try:
        body = sys.stdin.buffer.read().decode("utf-8-sig")
        req = json.loads(body)
        if not isinstance(req, dict):
            result = err("INVALID_INPUT", "stdin must contain a JSON object.")
        else:
            result = main(req)
    except (json.JSONDecodeError, UnicodeError):
        result = err("INVALID_INPUT", "stdin must contain a UTF-8 JSON object.")
    except (ValueError, OSError, RuntimeError) as e:
        result = err("OPERATION_FAILED", str(e))
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(run())

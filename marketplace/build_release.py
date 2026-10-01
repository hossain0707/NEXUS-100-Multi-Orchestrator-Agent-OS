"""Build and verify the upload-ready NEXUS-100 public plugin ZIP."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE / "nexus-100"
DIST = HERE / "dist"
MEMBERS = (
    "plugin.json",
    "mcp.json",
    "assets/icon.svg",
    "assets/logo.svg",
)
FORBIDDEN_PARTS = {
    ".env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source() -> tuple[str, str]:
    plugin = _load_json(PLUGIN_ROOT / "plugin.json")
    mcp = _load_json(PLUGIN_ROOT / "mcp.json")

    version = plugin["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise ValueError(f"plugin version is not semantic versioning: {version!r}")

    servers = mcp.get("mcpServers", {})
    if len(servers) != 1:
        raise ValueError("public submission package must declare exactly one MCP server")
    _, server = next(iter(servers.items()))
    if server.get("type") != "streamable-http":
        raise ValueError("MCP server must use streamable-http")
    endpoint = server.get("url", "")
    if not endpoint.startswith("https://") or "/mcp" not in endpoint:
        raise ValueError("MCP server URL must be the production HTTPS /mcp endpoint")

    for member in MEMBERS:
        source = PLUGIN_ROOT / member
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.is_symlink():
            raise ValueError(f"submission member may not be a symlink: {member}")
        text = source.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise ValueError(f"possible credential detected in {member}")

    return version, endpoint


def inspect_zip(output: Path) -> list[str]:
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("submission ZIP failed CRC validation")
        names = archive.namelist()
        if names != list(MEMBERS):
            raise ValueError(f"unexpected ZIP members: {names!r}")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe archive path: {name}")
            if any(part in FORBIDDEN_PARTS for part in path.parts):
                raise ValueError(f"forbidden archive member: {name}")
            if name.endswith((".env", ".pyc", ".p12", ".pem", ".key")):
                raise ValueError(f"forbidden archive member: {name}")
    return names


def main() -> Path:
    version, _ = validate_source()
    output = DIST / f"nexus-100-plugin-{version}.zip"
    DIST.mkdir(parents=True, exist_ok=True)

    for old in DIST.glob("nexus-100-plugin-*.zip"):
        if old != output:
            old.unlink()

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for member in MEMBERS:
            archive.write(PLUGIN_ROOT / member, arcname=member)

    members = inspect_zip(output)
    print(f"verified {output}: {', '.join(members)}")
    return output


if __name__ == "__main__":
    main()

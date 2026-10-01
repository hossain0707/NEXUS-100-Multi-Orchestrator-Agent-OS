"""Build the upload-ready NEXUS-100 public plugin ZIP."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE / "nexus-100"
DIST = HERE / "dist"


def main() -> Path:
    manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    output = DIST / f"nexus-100-plugin-{version}.zip"
    DIST.mkdir(parents=True, exist_ok=True)

    members = [
        "plugin.json",
        "mcp.json",
        "assets/icon.svg",
        "assets/logo.svg",
    ]

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for member in members:
            source = PLUGIN_ROOT / member
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, arcname=member)

    return output


if __name__ == "__main__":
    print(main())

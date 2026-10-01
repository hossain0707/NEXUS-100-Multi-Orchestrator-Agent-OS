import json
from pathlib import Path
from zipfile import ZipFile

from marketplace.build_release import MEMBERS, inspect_zip, main as build_release


ROOT = Path("marketplace/nexus-100")


def test_marketplace_manifest_is_submission_shaped():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    interface = manifest["extensions"]["com.openai"]["interface"]
    review = manifest["extensions"]["com.openai"]["review"]

    assert manifest["name"] == "nexus-100-agent-os"
    assert manifest["version"] == "1.0.1"
    assert len(manifest["description"]) <= 1024
    assert len(interface["displayName"]) <= 30
    assert len(interface["shortDescription"]) <= 30
    assert len(interface["longDescription"]) <= 4000
    assert len(interface["developerName"]) <= 80
    assert len(interface["capabilities"]) <= 20
    assert all(len(item) <= 120 for item in interface["capabilities"])
    assert len(interface["defaultPrompt"]) <= 3
    assert all(len(prompt) <= 128 for prompt in interface["defaultPrompt"])
    assert len(set(interface["defaultPrompt"])) == len(interface["defaultPrompt"])

    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        assert interface[key].startswith("https://")

    for key in ("logo", "composerIcon"):
        relative = interface[key]
        assert relative.startswith("./")
        assert (ROOT / relative[2:]).is_file()

    assert "screenshots" not in interface
    assert len(review["test_cases"]["positive"]) == 5
    assert len(review["test_cases"]["negative"]) == 3
    assert review["commerce"] is False
    # A real reviewer-accessible video must be supplied by the owner/portal.
    assert "demo_recording_url" not in review


def test_marketplace_mcp_manifest_points_to_one_production_server():
    manifest = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    assert len(manifest["mcpServers"]) == 1
    server = manifest["mcpServers"]["nexus-100"]

    assert server["type"] == "streamable-http"
    assert server["url"].startswith("https://")
    assert server["url"].endswith("/mcp/")


def test_release_zip_is_minimal_and_inspected(tmp_path, monkeypatch):
    import marketplace.build_release as release

    monkeypatch.setattr(release, "DIST", tmp_path)
    output = build_release()

    assert output.name == "nexus-100-plugin-1.0.1.zip"
    assert inspect_zip(output) == list(MEMBERS)

    with ZipFile(output) as archive:
        assert archive.namelist() == list(MEMBERS)
        assert not any(name.startswith(".") for name in archive.namelist())
        assert not any(".env" in name for name in archive.namelist())

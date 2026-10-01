import json
from pathlib import Path


ROOT = Path("marketplace/nexus-100")


def test_marketplace_manifest_is_submission_shaped():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    interface = manifest["extensions"]["com.openai"]["interface"]
    review = manifest["extensions"]["com.openai"]["review"]

    assert manifest["name"] == "nexus-100-agent-os"
    assert manifest["version"] == "1.0.0"
    assert len(interface["displayName"]) <= 30
    assert len(interface["shortDescription"]) <= 30
    assert len(interface["longDescription"]) <= 4000
    assert len(interface["capabilities"]) <= 20
    assert len(interface["defaultPrompt"]) <= 3
    assert all(len(prompt) <= 128 for prompt in interface["defaultPrompt"])

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


def test_marketplace_mcp_manifest_points_to_production_https():
    manifest = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    server = manifest["mcpServers"]["nexus-100"]

    assert server["type"] == "streamable-http"
    assert server["url"].startswith("https://")
    assert server["url"].endswith("/mcp/")

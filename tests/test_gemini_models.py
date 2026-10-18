"""Contract tests for optional Google Gemini free-tier model catalog support.

These tests never contact the Gemini API or consume paid quota.
"""

from nexus.model_catalog import _profile_for
from nexus.config import Settings


def test_gemini_flash_lite_is_supported_by_model_catalog():
    profile = _profile_for("gemini-2.5-flash-lite", source="configured", available=True)
    assert profile is not None
    assert profile.family == "fast"
    assert profile.available is True
    assert profile.source == "configured"


def test_gemini_flash_is_supported_by_model_catalog():
    profile = _profile_for("gemini-2.5-flash", source="provider", available=True)
    assert profile is not None
    assert profile.quality >= 0.90
    assert profile.family == "balanced"
    assert profile.source == "provider"


def test_gemini_provider_stays_off_by_default():
    config = Settings(_env_file=None)
    assert config.backend_model_execution_enabled is False

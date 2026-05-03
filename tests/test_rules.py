"""Unit tests for skill_linter rules R001-R004."""
from __future__ import annotations

from pathlib import Path

import pytest

from skill_linter.rules import (
    ALL_RULES,
    R001NoRasterImageEmbed,
    R002MermaidNeedsFallback,
    R003NoSecrets,
    R004HasHarness,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _violations(rule, path: Path):
    return list(rule.check(path, path.read_text(encoding="utf-8")))


def test_good_skill_passes_all_rules():
    good = FIXTURES / "good_skill.md"
    for rule in ALL_RULES:
        v = _violations(rule, good)
        assert not v, f"good fixture flagged by {rule.code}: {v}"


def test_r001_catches_raster_image_embed():
    bad = FIXTURES / "bad_skill_with_image.md"
    violations = _violations(R001NoRasterImageEmbed(), bad)
    assert len(violations) == 1
    assert violations[0].code == "R001"
    assert "пирожки" in violations[0].msg or "image" in violations[0].msg


def test_r002_catches_mermaid_without_fallback():
    bad = FIXTURES / "bad_skill_with_image.md"
    violations = _violations(R002MermaidNeedsFallback(), bad)
    assert len(violations) == 1
    assert violations[0].code == "R002"


def test_r003_catches_github_pat():
    bad = FIXTURES / "bad_skill_with_image.md"
    violations = _violations(R003NoSecrets(), bad)
    assert any("PAT" in v.msg for v in violations), violations


def test_r004_catches_missing_harness():
    bad = FIXTURES / "missing_harness_skill.md"
    violations = _violations(R004HasHarness(), bad)
    assert len(violations) == 1
    assert violations[0].code == "R004"


@pytest.mark.parametrize("rule_class", [
    R001NoRasterImageEmbed, R002MermaidNeedsFallback,
    R003NoSecrets, R004HasHarness,
])
def test_rules_have_code_and_description(rule_class):
    rule = rule_class()
    assert rule.code.startswith("R0")
    assert rule.description

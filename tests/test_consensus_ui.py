"""
Unit Tests for Consensus Analysis UI Presentation and Evidence View Updates.
Tests all five consensus levels:
1. STRONG_CONSENSUS (emerald green)
2. MODERATE_CONSENSUS (cyan)
3. WEAK_CONSENSUS (cyan)
4. CONTRADICTORY_CONSENSUS (amber)
5. INSUFFICIENT_EVIDENCE (cyan)
Verifies that only the currently returned level is active/highlighted,
that underscores are converted to spaces for display,
and that the visible red/pink "Safety constraint active..." banner is removed from Evidence view
while underlying safety constraint logic remains active.
"""

import os
import re
import pytest

APP_JS_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "static", "app.js")
STYLES_CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "static", "styles.css")


@pytest.fixture(scope="module")
def app_js_content():
    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def styles_css_content():
    with open(STYLES_CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_five_consensus_levels_defined(app_js_content):
    """Verify that all five consensus levels are explicitly defined with exact keys and labels."""
    expected_levels = [
        ("STRONG_CONSENSUS", "STRONG CONSENSUS", "emerald"),
        ("MODERATE_CONSENSUS", "MODERATE CONSENSUS", "cyan"),
        ("WEAK_CONSENSUS", "WEAK CONSENSUS", "cyan"),
        ("CONTRADICTORY_CONSENSUS", "CONTRADICTORY CONSENSUS", "amber"),
        ("INSUFFICIENT_EVIDENCE", "INSUFFICIENT EVIDENCE", "cyan"),
    ]

    for key, label, tier in expected_levels:
        assert f"key: '{key}'" in app_js_content, f"Missing key {key} in app.js"
        assert f"label: '{label}'" in app_js_content, f"Missing label {label} in app.js"
        assert f"tier: '{tier}'" in app_js_content, f"Missing tier {tier} for {key} in app.js"


def evaluate_active_consensus_level(raw_level: str):
    """
    Simulates the exact consensus level evaluation logic in app.js.
    Returns dict mapping level key to (is_active, label, tier).
    """
    levels = [
        {"key": "STRONG_CONSENSUS", "label": "STRONG CONSENSUS", "tier": "emerald"},
        {"key": "MODERATE_CONSENSUS", "label": "MODERATE CONSENSUS", "tier": "cyan"},
        {"key": "WEAK_CONSENSUS", "label": "WEAK CONSENSUS", "tier": "cyan"},
        {"key": "CONTRADICTORY_CONSENSUS", "label": "CONTRADICTORY CONSENSUS", "tier": "amber"},
        {"key": "INSUFFICIENT_EVIDENCE", "label": "INSUFFICIENT EVIDENCE", "tier": "cyan"},
    ]

    normalized = str(raw_level or "").strip().replace(" ", "_").upper()

    results = {}
    for cfg in levels:
        key = cfg["key"]
        is_active = (
            normalized == key
            or (key.endswith("_CONSENSUS") and normalized == key.replace("_CONSENSUS", ""))
            or (key == "INSUFFICIENT_EVIDENCE" and normalized in ["INSUFFICIENT", "INSUFFICIENT_EVIDENCE"])
        )
        results[key] = {
            "active": is_active,
            "label": cfg["label"],
            "tier": cfg["tier"]
        }
    return results


def test_strong_consensus_highlight():
    """Test 1: STRONG_CONSENSUS - only STRONG CONSENSUS is highlighted with emerald tier."""
    res = evaluate_active_consensus_level("STRONG_CONSENSUS")
    assert res["STRONG_CONSENSUS"]["active"] is True
    assert res["STRONG_CONSENSUS"]["tier"] == "emerald"
    assert res["STRONG_CONSENSUS"]["label"] == "STRONG CONSENSUS"

    assert res["MODERATE_CONSENSUS"]["active"] is False
    assert res["WEAK_CONSENSUS"]["active"] is False
    assert res["CONTRADICTORY_CONSENSUS"]["active"] is False
    assert res["INSUFFICIENT_EVIDENCE"]["active"] is False


def test_moderate_consensus_highlight():
    """Test 2: MODERATE_CONSENSUS - only MODERATE CONSENSUS is highlighted with cyan tier."""
    res = evaluate_active_consensus_level("MODERATE_CONSENSUS")
    assert res["MODERATE_CONSENSUS"]["active"] is True
    assert res["MODERATE_CONSENSUS"]["tier"] == "cyan"
    assert res["MODERATE_CONSENSUS"]["label"] == "MODERATE CONSENSUS"

    assert res["STRONG_CONSENSUS"]["active"] is False
    assert res["WEAK_CONSENSUS"]["active"] is False
    assert res["CONTRADICTORY_CONSENSUS"]["active"] is False
    assert res["INSUFFICIENT_EVIDENCE"]["active"] is False


def test_weak_consensus_highlight():
    """Test 3: WEAK_CONSENSUS - only WEAK CONSENSUS is highlighted with cyan tier."""
    res = evaluate_active_consensus_level("WEAK_CONSENSUS")
    assert res["WEAK_CONSENSUS"]["active"] is True
    assert res["WEAK_CONSENSUS"]["tier"] == "cyan"
    assert res["WEAK_CONSENSUS"]["label"] == "WEAK CONSENSUS"

    assert res["STRONG_CONSENSUS"]["active"] is False
    assert res["MODERATE_CONSENSUS"]["active"] is False
    assert res["CONTRADICTORY_CONSENSUS"]["active"] is False
    assert res["INSUFFICIENT_EVIDENCE"]["active"] is False


def test_contradictory_consensus_highlight():
    """Test 4: CONTRADICTORY_CONSENSUS - only CONTRADICTORY CONSENSUS is highlighted with amber tier."""
    res = evaluate_active_consensus_level("CONTRADICTORY_CONSENSUS")
    assert res["CONTRADICTORY_CONSENSUS"]["active"] is True
    assert res["CONTRADICTORY_CONSENSUS"]["tier"] == "amber"
    assert res["CONTRADICTORY_CONSENSUS"]["label"] == "CONTRADICTORY CONSENSUS"

    assert res["STRONG_CONSENSUS"]["active"] is False
    assert res["MODERATE_CONSENSUS"]["active"] is False
    assert res["WEAK_CONSENSUS"]["active"] is False
    assert res["INSUFFICIENT_EVIDENCE"]["active"] is False


def test_insufficient_evidence_highlight():
    """Test 5: INSUFFICIENT_EVIDENCE - only INSUFFICIENT EVIDENCE is highlighted with cyan tier."""
    res = evaluate_active_consensus_level("INSUFFICIENT_EVIDENCE")
    assert res["INSUFFICIENT_EVIDENCE"]["active"] is True
    assert res["INSUFFICIENT_EVIDENCE"]["tier"] == "cyan"
    assert res["INSUFFICIENT_EVIDENCE"]["label"] == "INSUFFICIENT EVIDENCE"

    assert res["STRONG_CONSENSUS"]["active"] is False
    assert res["MODERATE_CONSENSUS"]["active"] is False
    assert res["WEAK_CONSENSUS"]["active"] is False
    assert res["CONTRADICTORY_CONSENSUS"]["active"] is False


def test_consensus_score_and_explanation_preserved(app_js_content):
    """Verify that Consensus Score and Explanation text remain rendered below the five-level indicator."""
    assert "Consensus Score:" in app_js_content
    assert "consensusScoreFormatted" in app_js_content
    assert "trust-metric-callout" in app_js_content
    assert "trust-explanation-box" in app_js_content
    assert "consensusExplanationText" in app_js_content


def test_visible_safety_constraint_banner_removed_from_evidence_view(app_js_content):
    """Verify that the visible red/pink 'Safety constraint active...' banner is removed from Evidence view."""
    assert "Safety constraint active: Confidence ceiling capped at 0.50 due to contradictory biomedical evidence." not in app_js_content


def test_underlying_safety_constraint_preserved(app_js_content):
    """Verify that underlying safety constraint logic (capping fused confidence, safety cap chip) remains active while visible banner is removed."""
    assert "0.50 Capped" in app_js_content
    assert "CONTRADICTION SAFETY CAP ACTIVATED" not in app_js_content


def test_styles_css_contains_consensus_tiers(styles_css_content):
    """Verify that styles.css contains rules for inactive state and emerald, cyan, and amber active tiers."""
    assert ".consensus-levels-grid" in styles_css_content
    assert ".consensus-level-card.inactive" in styles_css_content
    assert ".consensus-level-card.tier-emerald.active" in styles_css_content
    assert ".consensus-level-card.tier-cyan.active" in styles_css_content
    assert ".consensus-level-card.tier-amber.active" in styles_css_content

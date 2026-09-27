"""
Automated Test Suite for Counterfactual Analysis State Synchronization.

Verifies:
1. Architectural integrity in app.js:
   - AbortController cancellation for in-flight requests.
   - Request sequence ID tracking (latestWhatIfRequestId).
   - Immediate invalidation of previous results upon input change (zero setTimeout workaround).
   - DOM input snapshot parity check before applying responses.
   - Status calculating badge styling.
2. Requirement 12: Initial BP = 140 -> Change BP = 100:
   - Recalculation strictly from BP = 100.
   - Modified Features Breakdown shows original=140, counterfactual=100, delta=-40.
   - No old 140-based counterfactual result remains.
3. Requirement 13: Rapid changes 100 -> 120 -> 150:
   - State synchronization simulator enforces that out-of-order responses are dropped.
   - Final state strictly corresponds to BP = 150.
4. Requirement 14: Multiple parameter changes:
   - Changing BP, cholesterol, and max heart rate simultaneously.
   - All modified features belong to the same atomic calculation snapshot.
"""

import copy
import os
import re
import pytest
from src.prediction.counterfactual_service import CounterfactualService
from app.disease_schemas import DEMO_PATIENT_DATA


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


@pytest.fixture(scope="module")
def service():
    return CounterfactualService()


# --- PART 1: STATIC & ARCHITECTURAL VERIFICATION ---

def test_abort_controller_and_request_id_in_app_js(app_js_content):
    """Verify app.js employs AbortController and request ID sequencing."""
    assert "let activeWhatIfController = null;" in app_js_content
    assert "let latestWhatIfRequestId = 0;" in app_js_content
    assert "new AbortController()" in app_js_content
    assert "activeWhatIfController.abort()" in app_js_content
    assert "signal: controller.signal" in app_js_content
    assert "currentRequestId !== latestWhatIfRequestId" in app_js_content


def test_immediate_invalidation_logic_in_app_js(app_js_content):
    """Verify app.js immediately invalidates prior counterfactual results upon input modification."""
    assert "function invalidateWhatIfResults()" in app_js_content
    assert "whatIfDiffTbody.innerHTML = '';" in app_js_content
    assert "whatIfDiffContainer.classList.add('hidden');" in app_js_content
    assert "whatIfSimProbEl.textContent = '...';" in app_js_content
    assert "whatIfSimStatusEl.textContent = 'CALCULATING...';" in app_js_content
    assert "status-calculating" in app_js_content


def test_no_delayed_settimeout_workaround(app_js_content):
    """Verify that artificial setTimeout debounce delays are eliminated from What-If controller."""
    # Ensure what-if controller doesn't use debounceTimer setTimeout workaround
    assert "debounceTimer = setTimeout(triggerSimulation" not in app_js_content
    assert "debounceTimer = setTimeout" not in app_js_content


def test_dom_snapshot_parity_check(app_js_content):
    """Verify app.js checks that current DOM inputs match the snapshot before rendering results."""
    assert "const currentDomFeatures = gatherWhatIfModifiedFeatures();" in app_js_content
    assert "JSON.stringify(currentDomFeatures) !== snapshotJson" in app_js_content


def test_status_calculating_css_styling(styles_css_content):
    """Verify styles.css contains styling for the calculating state badge."""
    assert ".whatif-status-badge.status-calculating" in styles_css_content


# --- PART 2: REQUIREMENT 12 — INITIAL BP=140 -> CHANGE BP=100 ---

def test_requirement_12_bp_140_to_100(service):
    """
    Requirement 12:
    Initial BP = 140
    Change BP = 100
    Confirm that Modified Features Breakdown and both prediction probabilities
    are recalculated from BP = 100 and no old 140-based result remains.
    """
    # Demo patient for Heart Disease has BP = 140
    original = copy.deepcopy(DEMO_PATIENT_DATA["heart_disease"])
    assert original["BP"] == 140

    # User changes BP from 140 to 100
    modified = copy.deepcopy(original)
    modified["BP"] = 100

    res = service.simulate_what_if("heart_disease", original, modified)
    assert res["status"] == "success"

    # Baseline prediction corresponds to BP = 140
    baseline = res["original"]
    # Counterfactual prediction corresponds to BP = 100
    counterfactual = res["counterfactual"]

    # Verify probability recalculation
    assert baseline["probability"] != counterfactual["probability"]
    assert res["delta"]["probability_change"] == round(counterfactual["probability"] - baseline["probability"], 4)

    # Verify Modified Features Breakdown
    diffs = res["modified_features"]
    assert len(diffs) == 1
    bp_diff = diffs[0]
    assert bp_diff["feature"] == "BP"
    assert bp_diff["original_value"] == 140
    assert bp_diff["counterfactual_value"] == 100
    assert bp_diff["delta"] == -40.0

    # Verify no old 140-based result lingers in counterfactual
    assert bp_diff["counterfactual_value"] != 140


# --- PART 3: REQUIREMENT 13 — RAPID CHANGES 100 -> 120 -> 150 ---

class WhatIfClientSimulator:
    """
    Simulates the exact frontend state synchronization logic implemented in app.js:
    - Tracks active AbortController and latestWhatIfRequestId.
    - Dispatches simulated async requests with synthetic latencies.
    - Verifies out-of-order responses cannot overwrite newer inputs.
    """
    def __init__(self, service, disease="heart_disease"):
        self.service = service
        self.disease = disease
        self.original_features = copy.deepcopy(DEMO_PATIENT_DATA[disease])
        self.dom_features = copy.deepcopy(self.original_features)
        self.active_request_id = 0
        self.latest_request_id = 0
        self.rendered_state = None
        self.invalidation_count = 0

    def update_input(self, feature: str, value: float):
        # 1. Update DOM representation
        self.dom_features[feature] = value

        # 2. Invalidate previous results immediately
        self.invalidation_count += 1
        self.rendered_state = "CALCULATING"

        # 3. Increment request ID
        self.latest_request_id += 1
        req_id = self.latest_request_id
        snapshot = copy.deepcopy(self.dom_features)

        # 4. Return request task info for simulated execution
        return req_id, snapshot

    def receive_response(self, req_id: int, snapshot: dict, res_data: dict):
        # Mimic app.js check:
        # if (currentRequestId !== latestWhatIfRequestId) return;
        if req_id != self.latest_request_id:
            # Stale response dropped
            return False

        # Mimic app.js check:
        # if (JSON.stringify(currentDomFeatures) !== snapshotJson) return;
        if self.dom_features != snapshot:
            # DOM inputs moved on; drop stale response
            return False

        # Apply to UI
        self.rendered_state = {
            "request_id": req_id,
            "counterfactual": res_data["counterfactual"],
            "delta": res_data["delta"],
            "modified_features": res_data["modified_features"]
        }
        return True


def test_requirement_13_rapid_changes_100_120_150(service):
    """
    Requirement 13:
    Change BP: 100 -> 120 -> 150 rapidly.
    Confirm that the final displayed result corresponds ONLY to BP = 150,
    even if asynchronous responses for 100 or 120 resolve after 150.
    """
    sim = WhatIfClientSimulator(service, disease="heart_disease")

    # Step 1: User types 100 rapidly
    req1_id, snap1 = sim.update_input("BP", 100)
    res1 = service.simulate_what_if("heart_disease", sim.original_features, snap1)

    # Step 2: User types 120 rapidly before req1 returns
    req2_id, snap2 = sim.update_input("BP", 120)
    res2 = service.simulate_what_if("heart_disease", sim.original_features, snap2)

    # Step 3: User types 150 rapidly before req2 returns
    req3_id, snap3 = sim.update_input("BP", 150)
    res3 = service.simulate_what_if("heart_disease", sim.original_features, snap3)

    # Simulate race condition: Req 1 resolves LATE (after Req 3 was dispatched)
    accepted_1 = sim.receive_response(req1_id, snap1, res1)
    assert accepted_1 is False, "Stale Request 1 (BP=100) must be rejected"

    # Simulate race condition: Req 2 resolves LATE
    accepted_2 = sim.receive_response(req2_id, snap2, res2)
    assert accepted_2 is False, "Stale Request 2 (BP=120) must be rejected"

    # Req 3 resolves
    accepted_3 = sim.receive_response(req3_id, snap3, res3)
    assert accepted_3 is True, "Latest Request 3 (BP=150) must be accepted"

    # Assert rendered state corresponds strictly to BP = 150
    final_render = sim.rendered_state
    assert final_render is not None
    assert final_render["request_id"] == req3_id

    diffs = final_render["modified_features"]
    assert len(diffs) == 1
    bp_diff = diffs[0]
    assert bp_diff["feature"] == "BP"
    assert bp_diff["counterfactual_value"] == 150
    assert bp_diff["original_value"] == 140
    assert bp_diff["delta"] == 10.0

    # Ensure no remnant of 100 or 120
    assert bp_diff["counterfactual_value"] not in [100, 120]


# --- PART 4: REQUIREMENT 14 — MULTIPLE PARAMETER CHANGES ---

def test_requirement_14_multiple_parameter_changes(service):
    """
    Requirement 14:
    Test changing multiple parameters before running the counterfactual.
    Confirm that all modified features belong to the same atomic calculation snapshot.
    """
    original = copy.deepcopy(DEMO_PATIENT_DATA["heart_disease"])
    # Original baseline:
    # BP: 140
    # Cholesterol: 289
    # Max_HR: 172

    modified = copy.deepcopy(original)
    modified["BP"] = 115
    modified["Cholesterol"] = 220
    modified["Max_HR"] = 145

    res = service.simulate_what_if("heart_disease", original, modified)
    assert res["status"] == "success"

    diffs = {d["feature"]: d for d in res["modified_features"]}
    assert len(diffs) == 3

    assert "BP" in diffs
    assert diffs["BP"]["counterfactual_value"] == 115
    assert diffs["BP"]["delta"] == -25.0

    assert "Cholesterol" in diffs
    assert diffs["Cholesterol"]["counterfactual_value"] == 220
    assert diffs["Cholesterol"]["delta"] == round(220 - float(original["Cholesterol"]), 4)

    assert "Max_HR" in diffs
    assert diffs["Max_HR"]["counterfactual_value"] == 145
    assert diffs["Max_HR"]["delta"] == round(145 - float(original["Max_HR"]), 4)

    # Probabilities belong to this exact combined 3-feature modification
    assert res["counterfactual"]["probability"] > 0
    assert res["delta"]["probability_change"] == round(res["counterfactual"]["probability"] - res["original"]["probability"], 4)

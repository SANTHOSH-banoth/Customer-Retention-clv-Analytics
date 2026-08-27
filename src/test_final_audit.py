"""
Phase 26 - Test for final data quality audit consistency.

Run with: python3 -m pytest src/test_final_audit.py -v
"""

from final_audit import reverify_headline_figures, EXPECTED


def test_all_headline_figures_match_prior_phase_reports():
    actual = reverify_headline_figures()
    for key, expected_val in EXPECTED.items():
        actual_val = actual[key]
        if isinstance(expected_val, float):
            assert abs(actual_val - expected_val) < 0.01, f"{key} drifted: expected {expected_val}, got {actual_val}"
        else:
            assert actual_val == expected_val, f"{key} drifted: expected {expected_val}, got {actual_val}"

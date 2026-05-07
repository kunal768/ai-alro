"""Tests for reasoner_agent/reasoning.py — _parse_conclusion() parser."""
import pytest

from reasoner_agent.reasoning import _parse_conclusion

FALLBACK_ID = "WH-SF01::DRV-001"


# ── Well-formed conclusion blocks ──────────────────────────────────────────────

class TestParseWellFormed:
    def test_confirm_no_flags(self):
        text = """
## SIGNAL ANALYSIS
Some analysis...

<conclusion>
DECISION: confirm
RECOMMENDED_OPTION: WH-SF01::DRV-001
FLAGS: NONE
OVERRIDE_REASON: NONE
</conclusion>
"""
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "confirm"
        assert result["recommended_option"] == "WH-SF01::DRV-001"
        assert result["flags"] == []
        assert result["override_reason"] is None
        assert result["parse_ok"] is True

    def test_qualify_with_flags(self):
        text = """
<conclusion>
DECISION: qualify
RECOMMENDED_OPTION: WH-OAK01::DRV-009
FLAGS: tight time window, high complaint rate
OVERRIDE_REASON: NONE
</conclusion>
"""
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "qualify"
        assert result["recommended_option"] == "WH-OAK01::DRV-009"
        assert "tight time window" in result["flags"]
        assert "high complaint rate" in result["flags"]
        assert result["override_reason"] is None

    def test_override_with_reason(self):
        text = """
<conclusion>
DECISION: override
RECOMMENDED_OPTION: WH-OAK01::DRV-009
FLAGS: driver unfamiliar with zone
OVERRIDE_REASON: Driver has no zone_familiarity for outer_east and the zone has a 14% complaint rate.
</conclusion>
"""
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "override"
        assert result["recommended_option"] == "WH-OAK01::DRV-009"
        assert result["override_reason"] is not None
        assert "outer_east" in result["override_reason"]
        assert "driver unfamiliar with zone" in result["flags"]

    def test_parse_ok_true_when_block_present(self):
        text = """
<conclusion>
DECISION: confirm
RECOMMENDED_OPTION: WH-SF01::DRV-001
FLAGS: NONE
OVERRIDE_REASON: NONE
</conclusion>
"""
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["parse_ok"] is True


# ── Case-insensitive robustness ────────────────────────────────────────────────

class TestCaseInsensitive:
    def test_uppercase_decision(self):
        text = "<conclusion>\nDECISION: CONFIRM\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "confirm"

    def test_mixed_case_conclusion_tag(self):
        text = "<CONCLUSION>\nDECISION: qualify\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</CONCLUSION>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["parse_ok"] is True

    def test_lowercase_none_in_flags(self):
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: none\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["flags"] == []

    def test_lowercase_none_in_override_reason(self):
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: NONE\nOVERRIDE_REASON: none.\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["override_reason"] is None


# ── Fallback behaviour when block is missing ───────────────────────────────────

class TestMissingBlock:
    def test_no_conclusion_block_parse_ok_false(self):
        text = "DECISION: confirm\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: NONE\nOVERRIDE_REASON: NONE"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["parse_ok"] is False

    def test_no_decision_defaults_to_qualify(self):
        text = "<conclusion>\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "qualify"

    def test_none_recommended_option_falls_back(self):
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: NONE\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["recommended_option"] == FALLBACK_ID

    def test_none_keyword_recommended_option_falls_back(self):
        # The documented way to signal no option: use the keyword NONE
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: NONE\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["recommended_option"] == FALLBACK_ID

    def test_empty_text_uses_fallback(self):
        result = _parse_conclusion("", FALLBACK_ID)
        assert result["recommended_option"] == FALLBACK_ID
        assert result["parse_ok"] is False


# ── Punctuation and whitespace robustness ──────────────────────────────────────

class TestPunctuationRobustness:
    def test_backtick_in_option_id_stripped(self):
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: `WH-SF01::DRV-001`\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["recommended_option"] == "WH-SF01::DRV-001"

    def test_bracket_in_option_id_stripped(self):
        text = "<conclusion>\nDECISION: confirm\nRECOMMENDED_OPTION: [WH-SF01::DRV-001]\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["recommended_option"] == "WH-SF01::DRV-001"

    def test_multiple_flags_parsed(self):
        text = "<conclusion>\nDECISION: qualify\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: risk A, risk B, risk C\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert len(result["flags"]) == 3

    def test_single_flag_parsed(self):
        text = "<conclusion>\nDECISION: qualify\nRECOMMENDED_OPTION: WH-SF01::DRV-001\nFLAGS: fragile cargo on motorbike\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert len(result["flags"]) == 1
        assert "fragile cargo on motorbike" in result["flags"]

    def test_extra_whitespace_around_decision(self):
        text = "<conclusion>\nDECISION:   override   \nRECOMMENDED_OPTION: WH-OAK01::DRV-009\nFLAGS: NONE\nOVERRIDE_REASON: NONE\n</conclusion>"
        result = _parse_conclusion(text, FALLBACK_ID)
        assert result["decision"] == "override"

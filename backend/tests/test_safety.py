"""Unit tests for the safety guardrails module."""

import pytest
from app.services.safety import check_safety, _check_advice, _has_doctor_reminder, DISCLAIMER


class TestCheckAdvice:
    def test_catches_you_should_take(self):
        assert _check_advice("You should take this medicine daily.")

    def test_catches_stop_taking(self):
        assert _check_advice("Stop taking this medication immediately.")

    def test_catches_i_recommend(self):
        assert _check_advice("I recommend increasing your dosage.")

    def test_catches_you_must(self):
        assert _check_advice("You must see a specialist right away.")

    def test_catches_increase_dose(self):
        assert _check_advice("You should increase your dose to 500mg.")

    def test_allows_normal_explanation(self):
        text = "This test measures your blood sugar levels over time."
        assert _check_advice(text) == ""

    def test_allows_factual_statements(self):
        text = "A1C levels below 5.7% are considered normal."
        assert _check_advice(text) == ""


class TestHasDoctorReminder:
    def test_detects_doctor_mention(self):
        text = "This is normal. Talk to your doctor if you have concerns."
        assert _has_doctor_reminder(text) is True

    def test_detects_nurse_mention(self):
        text = "Ask your nurse about next steps."
        assert _has_doctor_reminder(text) is True

    def test_detects_pharmacist(self):
        text = "Check with your pharmacist for more information."
        assert _has_doctor_reminder(text) is True

    def test_detects_healthcare_provider(self):
        text = "Discuss this with your healthcare provider."
        assert _has_doctor_reminder(text) is True

    def test_fails_when_no_reminder(self):
        text = "Your cholesterol is a bit high. Eat more vegetables."
        assert _has_doctor_reminder(text) is False


class TestCheckSafety:
    def test_passes_clean_text(self):
        text = "This test checks your blood sugar. Talk to your doctor if you have questions."
        result = check_safety(text)
        assert result["passed"] is True
        assert len(result["warnings"]) == 0

    def test_adds_disclaimer_when_missing(self):
        text = "Your cholesterol level is above the normal range."
        result = check_safety(text)
        assert DISCLAIMER.strip() in result["text"]
        assert any("disclaimer" in w.lower() for w in result["warnings"])

    def test_flags_medical_advice(self):
        text = "You should stop taking your medication. Talk to your doctor."
        result = check_safety(text)
        assert any("medical advice" in w.lower() for w in result["warnings"])

    def test_does_not_double_add_disclaimer(self):
        text = "Everything looks normal. Please talk to your doctor if worried."
        result = check_safety(text)
        assert result["text"].count("talk to your doctor") <= 2  # original + maybe disclaimer

    def test_flags_short_response(self):
        result = check_safety("OK.")
        assert any("too short" in w.lower() for w in result["warnings"])

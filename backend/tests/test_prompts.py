"""Unit tests for prompt templates."""

import pytest
from app.services.prompts import (
    SYSTEM_PROMPT,
    build_observation_prompt,
    build_condition_prompt,
    build_medication_prompt,
    build_general_prompt,
)


class TestSystemPrompt:
    def test_has_reading_level_instruction(self):
        assert "6th" in SYSTEM_PROMPT or "8th" in SYSTEM_PROMPT

    def test_has_no_advice_rule(self):
        assert "diagnose" in SYSTEM_PROMPT.lower() or "medical advice" in SYSTEM_PROMPT.lower()

    def test_has_doctor_reminder_rule(self):
        assert "doctor" in SYSTEM_PROMPT.lower()


class TestObservationPrompt:
    def test_includes_all_fields(self):
        prompt = build_observation_prompt(
            display="Total Cholesterol",
            value=215,
            unit="mg/dL",
            date="2024-03-15",
            flag="H",
            context="Cholesterol is a waxy substance...",
        )
        assert "Total Cholesterol" in prompt
        assert "215" in prompt
        assert "mg/dL" in prompt
        assert "2024-03-15" in prompt
        assert "abnormal" in prompt  # flag line
        assert "Cholesterol is a waxy substance" in prompt

    def test_no_flag_line_when_empty(self):
        prompt = build_observation_prompt(
            display="Body Height", value=170, unit="cm",
            date="2024-01-01", flag="", context="Some context.",
        )
        assert "abnormal" not in prompt


class TestConditionPrompt:
    def test_includes_all_fields(self):
        prompt = build_condition_prompt(
            display="Diabetes mellitus type 2",
            status="active",
            date="2020-06-01",
            context="Type 2 diabetes is a chronic condition...",
        )
        assert "Diabetes mellitus type 2" in prompt
        assert "active" in prompt
        assert "2020-06-01" in prompt
        assert "chronic condition" in prompt


class TestMedicationPrompt:
    def test_includes_all_fields(self):
        prompt = build_medication_prompt(
            display="Metformin 500 MG",
            instructions="Take twice daily with meals",
            date="2024-01-15",
            context="Metformin helps control blood sugar...",
        )
        assert "Metformin 500 MG" in prompt
        assert "twice daily" in prompt
        assert "2024-01-15" in prompt
        assert "blood sugar" in prompt


class TestGeneralPrompt:
    def test_includes_term_and_context(self):
        prompt = build_general_prompt(
            term="Hypertension",
            context="High blood pressure is when...",
        )
        assert "Hypertension" in prompt
        assert "High blood pressure" in prompt

    def test_includes_patient_context_when_provided(self):
        prompt = build_general_prompt(
            term="A1C",
            context="A1C measures blood sugar...",
            patient_context="This appeared in my lab results",
        )
        assert "lab results" in prompt

    def test_omits_patient_context_when_empty(self):
        prompt = build_general_prompt(
            term="A1C", context="A1C measures...", patient_context="",
        )
        assert "Patient context" not in prompt

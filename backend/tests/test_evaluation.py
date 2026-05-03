"""Unit tests for the evaluation module."""

import pytest
from app.services.evaluation import (
    score_readability, detect_jargon, check_faithfulness,
    evaluate_explanation, format_report,
    TARGET_FK_GRADE, TARGET_READING_EASE,
)


class TestScoreReadability:
    def test_simple_text_scores_low(self):
        text = "Your blood sugar is high. This means your body has too much sugar in it. Talk to your doctor about what to do next."
        scores = score_readability(text)
        assert scores["flesch_kincaid_grade"] < 10
        assert scores["flesch_reading_ease"] > 40

    def test_complex_text_scores_higher(self):
        text = (
            "The patient presents with hyperglycemia secondary to insulin resistance, "
            "with glycosylated hemoglobin levels indicating suboptimal glycemic control "
            "over the preceding trimester."
        )
        scores = score_readability(text)
        assert scores["flesch_kincaid_grade"] > 10

    def test_returns_target_flags(self):
        text = "This is a simple test result. Everything looks good."
        scores = score_readability(text)
        assert "meets_grade_target" in scores
        assert "meets_ease_target" in scores
        assert isinstance(scores["meets_grade_target"], bool)

    def test_easy_text_meets_targets(self):
        text = "Your test is fine. Your sugar is good. Keep eating well. See your doctor next year."
        scores = score_readability(text)
        assert scores["meets_grade_target"] is True


class TestDetectJargon:
    def test_finds_unexplained_jargon(self):
        text = "You have hypertension and your renal function is declining."
        result = detect_jargon(text)
        assert "hypertension" in result["unexplained_terms"]
        assert "renal" in result["unexplained_terms"]

    def test_accepts_explained_jargon(self):
        text = "You have hypertension (high blood pressure) which is common."
        result = detect_jargon(text)
        assert "hypertension" not in result["unexplained_terms"]

    def test_accepts_jargon_with_which_means(self):
        text = "Your creatinine, which means a waste product from muscles, is normal."
        result = detect_jargon(text)
        assert "creatinine" not in result["unexplained_terms"]

    def test_no_jargon_in_clean_text(self):
        text = "Your blood sugar test came back normal. Keep up the good work."
        result = detect_jargon(text)
        assert result["total_jargon_found"] == 0

    def test_counts_total_found(self):
        text = "The patient has chronic hypertension and acute renal issues."
        result = detect_jargon(text)
        assert result["total_jargon_found"] >= 3  # chronic, hypertension, acute, renal


class TestCheckFaithfulness:
    def test_grounded_claims(self):
        explanation = "Your cholesterol is 215 mg/dL which is above 200 mg/dL."
        context = "Normal cholesterol is below 200 mg/dL. Levels above 240 are high."
        result = check_faithfulness(explanation, context)
        assert result["grounded"] is True

    def test_ungrounded_claims(self):
        explanation = "Your cholesterol of 350 mg/dL is dangerously high."
        context = "Normal cholesterol is below 200 mg/dL."
        result = check_faithfulness(explanation, context)
        # 350 doesn't appear in context
        assert len(result["ungrounded_claims"]) > 0

    def test_no_claims_is_grounded(self):
        explanation = "This test checks your blood sugar over time."
        context = "A1C measures average blood glucose."
        result = check_faithfulness(explanation, context)
        assert result["grounded"] is True


class TestEvaluateExplanation:
    def test_good_explanation_passes(self):
        text = "Your blood sugar is a bit high. This test checks sugar over three months. Talk to your doctor about next steps."
        result = evaluate_explanation(text)
        assert "readability" in result
        assert "jargon" in result
        assert "overall_pass" in result

    def test_jargon_heavy_text_may_fail(self):
        text = "Acute hepatic insufficiency with comorbid renal nephropathy and chronic bilateral edema."
        result = evaluate_explanation(text)
        assert len(result["jargon"]["unexplained_terms"]) > 2


class TestFormatReport:
    def test_report_contains_scores(self):
        scores = evaluate_explanation("Simple text. Talk to your doctor.")
        report = format_report(scores)
        assert "Flesch-Kincaid" in report
        assert "Reading Ease" in report
        assert "Jargon" in report

"""Hybrid audit pipeline: `salary`/`employment_type` come deterministically
from a `Work24StructuredPosting` record; `duties`/`tools_or_skills`/
`training_or_mentoring`/`probation_terms` come from an sLLM provider's
free-text extraction, validated by the exact same Evidence Harness as the
existing pipeline (TASK "Work24 Structured Data + sLLM Hybrid Audit
Pipeline").

This is an *additive* pipeline, not a replacement: `app.services.
audit_pipeline.analyze_posting` (the existing 6-field, provider-only path)
is untouched and still used for every posting_id that has no
Work24StructuredPosting record (see `app.api.v1.postings.analyze_by_id`,
which chooses between the two).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import ValidationError

from ..errors import AnalysisFailedError
from ..models.posting import AuditedField, PostingAnalysis, PostingInput, ValidationWarning, VerificationAction
from ..models.work24_structured import Work24StructuredPosting
from ..providers.base import FreeTextExtractionProvider
from ..providers.raw import RawFreeTextExtraction
from ..rules.field_rules import evaluate_confirmed
from .conflict_detection import detect_salary_conflict
from .evidence import EvidenceMismatchError, validate_evidence_span
from .structured_fields import build_employment_type_field, build_salary_field, build_work_hours_info
from .verification import build_verification_action

MAX_ATTEMPTS = 2  # one initial attempt + at most one retry -- same budget as the legacy pipeline


def _run_free_text_extraction(
    source_text: str, expected_occupation: Optional[str], provider: FreeTextExtractionProvider
) -> RawFreeTextExtraction:
    last_error: Optional[Exception] = None
    for _attempt in range(MAX_ATTEMPTS):
        raw = provider.extract_free_text(source_text, expected_occupation)
        try:
            candidate = RawFreeTextExtraction.model_validate(raw)
            for raw_field in candidate.fields:
                if raw_field.evidence_text is not None:
                    validate_evidence_span(source_text, raw_field.evidence_text, raw_field.start, raw_field.end)
        except (ValidationError, EvidenceMismatchError) as exc:
            last_error = exc
            continue
        return candidate

    raise AnalysisFailedError(
        "hybrid free-text extraction failed schema or evidence validation after one retry",
        details={"last_error": str(last_error)} if last_error else None,
    )


def analyze_posting_hybrid(
    posting: PostingInput,
    structured: Work24StructuredPosting,
    provider: FreeTextExtractionProvider,
) -> PostingAnalysis:
    fields: Dict[str, AuditedField] = {
        "salary": build_salary_field(structured),
        "employment_type": build_employment_type_field(structured),
    }

    validated = _run_free_text_extraction(posting.source_text, posting.expected_occupation, provider)

    warnings: List[ValidationWarning] = []
    actions: List[VerificationAction] = []

    for raw_field in validated.fields:
        final_status = raw_field.status
        evidence = None
        reason_code = "provider_absent" if final_status == "absent" else "provider_reported"

        if final_status != "absent":
            is_relevant, meets_confirmed, rule_reason = evaluate_confirmed(raw_field.field, raw_field.evidence_text)

            if not is_relevant:
                final_status = "absent"
                reason_code = rule_reason
                warnings.append(
                    ValidationWarning(
                        code="downgraded_to_absent",
                        field=raw_field.field,
                        message="evidence text did not match any field-relevant keyword; treated as absent",
                    )
                )
            else:
                evidence = {
                    "text": raw_field.evidence_text,
                    "start": raw_field.start,
                    "end": raw_field.end,
                }
                reason_code = rule_reason
                if raw_field.status == "confirmed" and not meets_confirmed:
                    final_status = "vague"
                    warnings.append(
                        ValidationWarning(
                            code="downgraded_to_vague",
                            field=raw_field.field,
                            message="evidence present but did not meet the deterministic confirmed criteria",
                        )
                    )

        fields[raw_field.field] = AuditedField(
            field=raw_field.field,
            status=final_status,
            evidence=evidence,
            reason_code=reason_code,
            provenance="SLM_EXTRACTED",
        )

    for field_name, audited in fields.items():
        if audited.status in ("vague", "absent"):
            actions.append(build_verification_action(field_name, audited.status))

    conflict_warning = detect_salary_conflict(posting.source_text, structured)
    if conflict_warning is not None:
        warnings.append(conflict_warning)

    return PostingAnalysis(
        posting_id=posting.posting_id,
        occupation=structured.occupation_name or posting.expected_occupation,
        employment_type=structured.employment_type,
        fields=fields,
        verification_actions=actions,
        validation_warnings=warnings,
        external_context=[],
        work_hours=build_work_hours_info(structured),
    )

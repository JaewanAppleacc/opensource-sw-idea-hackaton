"""Orchestrates: extraction -> schema validation -> evidence validation ->
deterministic field rules -> verification actions.

Provider or schema/evidence failures are never downgraded into a posting
status. A field's status is only ever downgraded (confirmed -> vague,
vague/confirmed -> absent) by an explicit, rubric-driven deterministic rule
in app.rules.field_rules -- never upgraded, and never invented.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import ValidationError

from ..errors import AnalysisFailedError
from ..models.posting import AuditedField, PostingAnalysis, PostingInput, ValidationWarning, VerificationAction
from ..providers.base import ExtractionProvider
from ..providers.raw import RawExtraction
from ..rules.field_rules import evaluate_confirmed
from .evidence import EvidenceMismatchError, validate_evidence_span
from .verification import build_verification_action

MAX_ATTEMPTS = 2  # one initial attempt + at most one retry


def analyze_posting(posting: PostingInput, provider: ExtractionProvider) -> PostingAnalysis:
    validated: Optional[RawExtraction] = None
    last_error: Optional[Exception] = None

    for _attempt in range(MAX_ATTEMPTS):
        raw = provider.extract(posting.source_text, posting.expected_occupation)
        try:
            candidate = RawExtraction.model_validate(raw)
            for raw_field in candidate.fields:
                if raw_field.evidence_text is not None:
                    validate_evidence_span(
                        posting.source_text, raw_field.evidence_text, raw_field.start, raw_field.end
                    )
        except (ValidationError, EvidenceMismatchError) as exc:
            last_error = exc
            continue
        validated = candidate
        break

    if validated is None:
        raise AnalysisFailedError(
            "structured extraction failed schema or evidence validation after one retry",
            details={"last_error": str(last_error)} if last_error else None,
        )

    fields: Dict[str, AuditedField] = {}
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
        )
        if final_status in ("vague", "absent"):
            actions.append(build_verification_action(raw_field.field, final_status))

    return PostingAnalysis(
        posting_id=posting.posting_id,
        occupation=validated.occupation or posting.expected_occupation,
        employment_type=validated.employment_type,
        fields=fields,
        verification_actions=actions,
        validation_warnings=warnings,
        external_context=[],
    )

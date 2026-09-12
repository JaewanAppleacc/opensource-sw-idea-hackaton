"""Typed application errors.

System/pipeline failures are never reported as a posting field status
(e.g. never silently mapped to "absent"). They surface as one of these
typed errors instead, each carrying a stable `code` from
`app.models.common.ErrorCode`.
"""
from __future__ import annotations

from typing import Optional

from .models.common import ErrorCode


class AppError(Exception):
    code: ErrorCode = "analysis_failed"
    status_code: int = 500

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidInputError(AppError):
    code: ErrorCode = "invalid_input"
    status_code = 422


class AnalysisFailedError(AppError):
    code: ErrorCode = "analysis_failed"
    status_code = 422


class ProviderUnavailableError(AppError):
    code: ErrorCode = "provider_unavailable"
    status_code = 503


class NoMatchFoundError(AppError):
    code: ErrorCode = "no_match_found"
    status_code = 404


class DataNotReadyError(AppError):
    code: ErrorCode = "data_not_ready"
    status_code = 200


class PrivateDataUnavailableError(AppError):
    """The requested posting_id has no private full text resolvable on this
    machine right now (data/private/intake_raw/<id>.json missing) -- e.g. a
    fresh clone with no private data staged. Never invented, never
    downgraded into a fake analysis; the caller must show its own
    fail-closed UI state.
    """

    code: ErrorCode = "private_data_unavailable"
    status_code = 503

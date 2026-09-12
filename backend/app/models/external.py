"""External context: factual, provenanced data points that sit alongside a
posting audit but never mutate a posting field's status.

Per CLAUDE.md: never infer actual salary from National Pension contribution
data, and never generate stability/growth/turnover/culture/risk scores.
This model only carries source, provenance, and stated limitations --
nothing evaluative.
"""
from __future__ import annotations

from typing import Union

from pydantic import Field

from .common import StrictModel


class ExternalContext(StrictModel):
    source: str = Field(..., min_length=1)
    reference_date: str = Field(..., description="ISO-8601 date the external figure was published or fetched.")
    description: str = Field(..., min_length=1)
    limitations: str = Field(..., min_length=1)
    values: dict[str, Union[float, str]] = Field(default_factory=dict)

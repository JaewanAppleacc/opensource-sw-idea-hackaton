from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.v1.router import api_router
from .errors import AppError
from .models.common import APIError

app = FastAPI(
    title="Jeonbuk Career Due-Diligence Backend",
    version="0.1.0",
    description=(
        "Audits a metropolitan-area posting against curated Jeonbuk postings using evidence-grounded "
        "field extraction, converts unresolved gaps into verification actions, and runs a deterministic "
        "hypothetical cash comparison. Not a company-rating or future-prediction service."
    ),
)

app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    error = APIError(code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(status_code=exc.status_code, content={"error": error.model_dump()})


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    error = APIError(
        code="invalid_input",
        message="request failed schema validation",
        details={"errors": jsonable_encoder(exc.errors())},
    )
    return JSONResponse(status_code=422, content={"error": error.model_dump()})

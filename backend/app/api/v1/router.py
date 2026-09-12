from __future__ import annotations

from fastapi import APIRouter

from . import data, finance, health, postings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(postings.router, tags=["postings"])
api_router.include_router(finance.router, tags=["finance"])
api_router.include_router(data.router, tags=["data"])

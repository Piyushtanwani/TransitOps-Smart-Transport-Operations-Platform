"""Shared schemas: paginated envelope + simple message."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Standard list envelope (docs/03 §1)."""

    items: list[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    message: str

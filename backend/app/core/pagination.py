"""Pagination + sort query params and a reusable `paginate` helper (docs/03 §1)."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session


@dataclass
class Pagination:
    page: int
    page_size: int
    sort: str | None
    order: str


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> Pagination:
    return Pagination(page=page, page_size=page_size, sort=sort, order=order)


def paginate(
    db: Session,
    stmt: Select,
    pg: Pagination,
    sortable: dict[str, InstrumentedAttribute],
    default: InstrumentedAttribute,
) -> tuple[list, int]:
    """Apply count + safe order-by (allowlisted columns only) + limit/offset."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.execute(count_stmt).scalar_one()
    col = sortable.get(pg.sort, default) if pg.sort else default
    stmt = stmt.order_by(col.desc() if pg.order == "desc" else col.asc())
    stmt = stmt.limit(pg.page_size).offset((pg.page - 1) * pg.page_size)
    rows = list(db.execute(stmt).scalars().all())
    return rows, int(total)

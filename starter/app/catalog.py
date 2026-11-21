"""Catalog read API — used by the Paayal voice tools (tool-token authenticated).

Only verified, active boats are ever exposed here; unverified listings are
invisible to callers by design (spec FR-02).
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import Boat, Operator

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


class BoatOut(BaseModel):
    id: int
    name: str
    operator_name: str
    capacity: int | None
    embarkation_point: str | None
    photo_urls: list[str]


def _to_out(boat: Boat, operator_name: str) -> BoatOut:
    return BoatOut(
        id=boat.id,
        name=boat.name,
        operator_name=operator_name,
        capacity=boat.capacity,
        embarkation_point=boat.embarkation_point,
        photo_urls=boat.photo_urls,
    )


@router.get("/boats", response_model=list[BoatOut])
def list_boats(request: Request, q: str | None = None):
    engine = request.app.state.engine
    with Session(engine) as session:
        stmt = (
            select(Boat, Operator.name)
            .join(Operator, Boat.operator_id == Operator.id)
            .where(Boat.active, Boat.verified_at.is_not(None), Operator.active)
        )
        rows = session.exec(stmt).all()
    boats = [_to_out(b, op) for b, op in rows]
    if q:
        needle = q.casefold()
        boats = [
            b for b in boats
            if needle in b.name.casefold()
            or needle in b.operator_name.casefold()
            or (b.embarkation_point and needle in b.embarkation_point.casefold())
        ]
    return boats


@router.get("/boats/{boat_id}", response_model=BoatOut)
def get_boat(boat_id: int, request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        row = session.exec(
            select(Boat, Operator.name)
            .join(Operator, Boat.operator_id == Operator.id)
            .where(
                Boat.id == boat_id,
                Boat.active,
                Boat.verified_at.is_not(None),
                Operator.active,
            )
        ).first()
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="boat_not_found")
    boat, op_name = row
    return _to_out(boat, op_name)

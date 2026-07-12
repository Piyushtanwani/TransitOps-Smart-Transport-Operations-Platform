"""Idempotent demo seed (docs/02 §7).

Run:  python -m app.db.seed [--force]

Without --force on a non-empty DB it is a friendly no-op. With --force it wipes the
domain tables (TRUNCATE ... RESTART IDENTITY CASCADE) and reloads a consistent
Indian-logistics fleet. Consistency invariants are asserted before commit.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, text

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.ai_settings import AISettings
from app.models.driver import Driver
from app.models.enums import (
    DriverStatus,
    ExpenseType,
    MaintenanceStatus,
    TripStatus,
    UserRole,
    VehicleStatus,
    VehicleType,
)
from app.models.expense import Expense
from app.models.fuel_log import FuelLog
from app.models.maintenance import MaintenanceLog
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle

TODAY = date.today()
NOW = datetime.now(timezone.utc)

_DOMAIN_TABLES = [
    "chat_messages",
    "chat_sessions",
    "audit_logs",
    "expenses",
    "fuel_logs",
    "maintenance_logs",
    "trips",
    "ai_settings",
    "drivers",
    "vehicles",
    "users",
]

# Default role→tool permission matrix (docs/06 §4). Admin UI edits this at runtime.
ROLE_TOOL_PERMISSIONS = {
    "fleet_manager": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_expiring_licenses", "get_vehicle_costs", "get_fuel_efficiency",
        "explain_business_rule",
    ],
    "driver": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_fuel_efficiency", "explain_business_rule",
    ],
    "safety_officer": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_expiring_licenses", "explain_business_rule",
    ],
    "financial_analyst": [
        "get_kpis", "get_vehicles", "get_drivers", "get_trips", "get_maintenance",
        "get_vehicle_costs", "get_fuel_efficiency", "explain_business_rule",
    ],
}

DEFAULT_SYSTEM_PROMPT = (
    "Be concise, professional and operational. Cite concrete numbers and identifiers "
    "from tool results. Never expose data a user's role may not access."
)

DEMO_LOGINS = [
    ("manager@transitops.in", "fleet_manager", "Meera Nair"),
    ("dispatch@transitops.in", "driver", "Piyush Rathod"),
    ("safety@transitops.in", "safety_officer", "Afif Khan"),
    ("finance@transitops.in", "financial_analyst", "Ismail Mansuri"),
]


def _d(x: str | int | float) -> Decimal:
    return Decimal(str(x))


def _next_trip_code(db) -> str:
    n = db.execute(text("SELECT nextval('trip_code_seq')")).scalar_one()
    return f"TRP-{int(n):04d}"


def _wipe(db) -> None:
    """Reset domain tables + the trip-code sequence (leaves alembic_version alone)."""
    db.execute(text(f"TRUNCATE {', '.join(_DOMAIN_TABLES)} RESTART IDENTITY CASCADE"))
    db.execute(text("ALTER SEQUENCE trip_code_seq RESTART WITH 1"))


def seed(force: bool = False) -> None:
    db = SessionLocal()
    try:
        existing = db.execute(select(func.count()).select_from(User)).scalar_one()
        if existing and not force:
            print(
                f"⚠️  Database already seeded ({existing} users). "
                "Re-run with --force to wipe and reload."
            )
            return

        _wipe(db)

        # ---- users ----
        pw = hash_password("Transit@123")
        users = {
            "manager": User(email="manager@transitops.in", hashed_password=pw,
                            full_name="Meera Nair", role=UserRole.fleet_manager),
            "dispatch": User(email="dispatch@transitops.in", hashed_password=pw,
                             full_name="Piyush Rathod", role=UserRole.driver),
            "safety": User(email="safety@transitops.in", hashed_password=pw,
                           full_name="Afif Khan", role=UserRole.safety_officer),
            "finance": User(email="finance@transitops.in", hashed_password=pw,
                            full_name="Ismail Mansuri", role=UserRole.financial_analyst),
        }
        db.add_all(users.values())
        db.flush()
        mgr, disp, fin = users["manager"].id, users["dispatch"].id, users["finance"].id

        # ---- vehicles (6 available, 2 on_trip, 1 in_shop, 1 retired) ----
        V = VehicleType
        S = VehicleStatus
        vspec = [
            ("GJ-01-AB-1234", "Tata Ace Van-05", V.van, 500, 42000, 650000, "North", S.available),
            ("GJ-05-CD-2201", "Ashok Leyland Dost", V.mini_truck, 1250, 88000, 950000, "West", S.available),
            ("MH-12-EF-8890", "Eicher Pro 2049", V.truck, 5000, 156000, 2200000, "West", S.on_trip),
            ("GJ-01-GH-3345", "Mahindra Blazo 28", V.truck, 18000, 98000, 3200000, "North", S.on_trip),
            ("RJ-14-IJ-5567", "BharatBenz 2823", V.truck, 16000, 120000, 2800000, "North", S.available),
            ("GJ-06-KL-7789", "Tata Prima Trailer", V.trailer, 25000, 210000, 3000000, "South", S.available),
            ("MH-04-MN-9911", "Ashok Leyland Ecomet", V.mini_truck, 2000, 64000, 1100000, "East", S.in_shop),
            ("GJ-27-OP-3312", "Tata 407 Van", V.van, 1500, 8000, 800000, "South", S.available),
            ("MP-09-QR-4456", "Eicher Pro 3015", V.truck, 9000, 45000, 1800000, "East", S.available),
            ("GJ-01-ST-6678", "Mahindra Bolero Pik-Up", V.mini_truck, 1000, 175000, 550000, "North", S.retired),
        ]
        vehicles = [
            Vehicle(registration_number=r, name=n, type=t, max_load_capacity_kg=_d(cap),
                    odometer_km=_d(odo), acquisition_cost=_d(acq), region=reg, status=st)
            for (r, n, t, cap, odo, acq, reg, st) in vspec
        ]
        db.add_all(vehicles)
        db.flush()

        # ---- drivers (incl. Alex valid, one expired, one suspended, one off_duty, two on_trip) ----
        DS = DriverStatus
        dspec = [
            ("Alex D'Souza", "GJ-LMV-2019-0001", "LMV", 400, 92, DS.available, "9876543210"),
            ("Ramesh Patel", "GJ-HMV-2016-0452", "HMV", 200, 85, DS.on_trip, "9812345678"),
            ("Suresh Yadav", "MH-HMV-2015-1120", "HMV", 150, 78, DS.on_trip, "9823456789"),
            ("Vikram Singh", "RJ-HMV-2014-3390", "HMV", -40, 66, DS.available, "9834567890"),
            ("Farhan Sheikh", "GJ-LMV-2018-7781", "LMV", 90, 58, DS.suspended, "9845678901"),
            ("Deepak Chauhan", "MP-MCWG-2020-2245", "MCWG", 300, 71, DS.off_duty, "9856789012"),
            ("Imran Khan", "GJ-HMV-2017-9934", "HMV", 500, 88, DS.available, "9867890123"),
            ("Sanjay Mehta", "MH-HMV-2013-6678", "HMV", 25, 95, DS.available, "9878901234"),
        ]
        drivers = [
            Driver(full_name=fn, license_number=ln, license_category=cat,
                   license_expiry=TODAY + timedelta(days=days), safety_score=_d(score),
                   status=st, contact_number=phone)
            for (fn, ln, cat, days, score, st, phone) in dspec
        ]
        db.add_all(drivers)
        db.flush()

        # ---- trips (8 completed, 2 dispatched, 3 draft, 1 cancelled) ----
        def mk_trip(vi, di, src, dst, cargo, dist, status, *, start=None, end=None,
                    revenue=0, days_ago=0, creator=disp):
            code = _next_trip_code(db)
            t = Trip(
                trip_code=code, source=src, destination=dst,
                vehicle_id=vehicles[vi].id, driver_id=drivers[di].id,
                cargo_weight_kg=_d(cargo), planned_distance_km=_d(dist),
                revenue=_d(revenue), status=status, created_by=creator,
                start_odometer=_d(start) if start is not None else None,
                end_odometer=_d(end) if end is not None else None,
            )
            stamp = NOW - timedelta(days=days_ago)
            if status == TripStatus.completed:
                t.dispatched_at = stamp - timedelta(hours=8)
                t.completed_at = stamp
            elif status == TripStatus.dispatched:
                t.dispatched_at = stamp
            elif status == TripStatus.cancelled:
                t.cancelled_at = stamp
            db.add(t)
            db.flush()
            return t

        completed = [
            mk_trip(0, 0, "Ahmedabad", "Surat", 450, 265, TripStatus.completed, start=41000, end=41265, revenue=12000, days_ago=50),
            mk_trip(1, 6, "Surat", "Mumbai", 1100, 290, TripStatus.completed, start=87000, end=87290, revenue=18000, days_ago=44),
            mk_trip(4, 1, "Mumbai", "Pune", 12000, 150, TripStatus.completed, start=119000, end=119150, revenue=35000, days_ago=39),
            mk_trip(5, 2, "Ahmedabad", "Indore", 22000, 400, TripStatus.completed, start=209000, end=209400, revenue=60000, days_ago=33),
            mk_trip(7, 0, "Rajkot", "Vadodara", 1200, 180, TripStatus.completed, start=7500, end=7680, revenue=9000, days_ago=27),
            mk_trip(8, 6, "Pune", "Ahmedabad", 8000, 650, TripStatus.completed, start=44000, end=44650, revenue=72000, days_ago=20),
            mk_trip(0, 7, "Vadodara", "Ahmedabad", 480, 110, TripStatus.completed, start=41265, end=41375, revenue=6500, days_ago=14),
            mk_trip(1, 0, "Mumbai", "Surat", 900, 290, TripStatus.completed, start=87290, end=87580, revenue=17000, days_ago=8),
        ]
        dispatched = [
            mk_trip(2, 1, "Ahmedabad", "Mumbai", 4500, 530, TripStatus.dispatched, start=156000, revenue=55000, days_ago=1),
            mk_trip(3, 2, "Surat", "Indore", 15000, 450, TripStatus.dispatched, start=98000, revenue=48000, days_ago=1),
        ]
        mk_trip(4, 6, "Ahmedabad", "Pune", 14000, 660, TripStatus.draft, revenue=0)
        mk_trip(8, 0, "Rajkot", "Mumbai", 7500, 620, TripStatus.draft, revenue=0)
        mk_trip(7, 7, "Vadodara", "Surat", 1400, 160, TripStatus.draft, revenue=0)
        mk_trip(1, 6, "Surat", "Rajkot", 1000, 340, TripStatus.cancelled, revenue=0, days_ago=6)

        # ---- maintenance (1 open on the in_shop vehicle, 4 closed) ----
        db.add(MaintenanceLog(vehicle_id=vehicles[6].id, title="Gearbox overhaul",
                              description="Complete gearbox strip and rebuild.",
                              cost=_d(0), status=MaintenanceStatus.open, created_by=mgr,
                              opened_at=NOW - timedelta(days=3)))
        closed_specs = [
            (0, "Oil & filter change", 1200, 55),
            (2, "Brake pad replacement", 8500, 40),
            (4, "Tyre replacement (x6)", 42000, 30),
            (5, "Clutch assembly repair", 15000, 18),
        ]
        for vi, title, cost, days_ago in closed_specs:
            opened = NOW - timedelta(days=days_ago)
            db.add(MaintenanceLog(vehicle_id=vehicles[vi].id, title=title, cost=_d(cost),
                                  status=MaintenanceStatus.closed, created_by=mgr,
                                  opened_at=opened, closed_at=opened + timedelta(days=1)))

        # ---- fuel logs: 8 linked to completed trips + standalone (≈20 total) ----
        for tr in completed:
            liters = (tr.end_odometer - tr.start_odometer) / _d(6)  # ~6 km/L
            db.add(FuelLog(vehicle_id=tr.vehicle_id, trip_id=tr.id, liters=liters.quantize(_d("0.01")),
                           cost=(liters * _d(100)).quantize(_d("0.01")),
                           odometer_at_fill=tr.end_odometer, created_by=disp,
                           filled_at=tr.completed_at.date()))
        standalone_fuel = [
            (0, 35, 3500, 48), (1, 60, 6000, 42), (4, 120, 12000, 36), (5, 180, 18000, 28),
            (8, 90, 9000, 22), (2, 140, 14000, 16), (3, 160, 16000, 10), (1, 55, 5500, 5),
            (0, 30, 3000, 3), (8, 85, 8500, 2), (4, 110, 11000, 1), (5, 175, 17500, 0),
        ]
        for vi, liters, cost, days_ago in standalone_fuel:
            db.add(FuelLog(vehicle_id=vehicles[vi].id, liters=_d(liters), cost=_d(cost),
                           created_by=disp, filled_at=TODAY - timedelta(days=days_ago)))

        # ---- expenses (~15: tolls, parking, fines, loading, other) ----
        espec = [
            (0, ExpenseType.toll, 450, 48), (1, ExpenseType.toll, 780, 44),
            (4, ExpenseType.toll, 1200, 40), (5, ExpenseType.parking, 200, 38),
            (2, ExpenseType.fine, 1500, 34), (8, ExpenseType.loading, 900, 30),
            (5, ExpenseType.toll, 1350, 26), (0, ExpenseType.parking, 150, 22),
            (1, ExpenseType.other, 600, 18), (4, ExpenseType.fine, 2000, 14),
            (3, ExpenseType.toll, 1650, 10), (8, ExpenseType.loading, 750, 7),
            (2, ExpenseType.toll, 980, 4), (5, ExpenseType.parking, 250, 2),
            (0, ExpenseType.toll, 420, 1),
        ]
        for vi, et, amt, days_ago in espec:
            db.add(Expense(vehicle_id=vehicles[vi].id, type=et, amount=_d(amt),
                           description=f"{et.value.title()} charge", created_by=fin,
                           incurred_at=TODAY - timedelta(days=days_ago)))

        # ---- ai_settings singleton ----
        db.add(AISettings(id=1, chatbot_enabled=True, model="anthropic/claude-3.5-haiku",
                          temperature=_d("0.30"), max_tokens=1024,
                          system_prompt=DEFAULT_SYSTEM_PROMPT,
                          role_tool_permissions=ROLE_TOOL_PERMISSIONS, updated_by=mgr))

        db.flush()
        _assert_invariants(db, dispatched, vehicles, drivers)
        db.commit()
        _print_summary(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _assert_invariants(db, dispatched, vehicles, drivers) -> None:
    """Fail loudly before commit if the demo dataset is internally inconsistent."""
    for tr in dispatched:
        veh = next(v for v in vehicles if v.id == tr.vehicle_id)
        drv = next(d for d in drivers if d.id == tr.driver_id)
        assert veh.status == VehicleStatus.on_trip, f"{veh.registration_number} not on_trip"
        assert drv.status == DriverStatus.on_trip, f"{drv.full_name} not on_trip"
    in_shop = [v for v in vehicles if v.status == VehicleStatus.in_shop]
    open_maint_vehicle_ids = {
        m.vehicle_id
        for m in db.execute(
            select(MaintenanceLog).where(MaintenanceLog.status == MaintenanceStatus.open)
        ).scalars()
    }
    for v in in_shop:
        assert v.id in open_maint_vehicle_ids, f"{v.registration_number} in_shop w/o open job"
    completed = db.execute(
        select(Trip).where(Trip.status == TripStatus.completed)
    ).scalars().all()
    for tr in completed:
        assert tr.end_odometer >= tr.start_odometer, f"{tr.trip_code} odometer regression"
    codes = sorted(
        db.execute(select(Trip.trip_code)).scalars().all()
    )
    assert codes[0] == "TRP-0001" and codes[-1] == f"TRP-{len(codes):04d}", "trip codes not sequential"


def _print_summary(db) -> None:
    def count(model) -> int:
        return db.execute(select(func.count()).select_from(model)).scalar_one()

    print("\n✅ Seed complete — TransitOps demo fleet loaded\n")
    print(f"  users            {count(User):>3}")
    print(f"  vehicles         {count(Vehicle):>3}")
    print(f"  drivers          {count(Driver):>3}")
    print(f"  trips            {count(Trip):>3}")
    print(f"  maintenance      {count(MaintenanceLog):>3}")
    print(f"  fuel_logs        {count(FuelLog):>3}")
    print(f"  expenses         {count(Expense):>3}")
    print("\n  Demo logins (password: Transit@123)")
    for email, role, name in DEMO_LOGINS:
        print(f"    {email:<26} {role:<18} {name}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the TransitOps demo dataset.")
    parser.add_argument("--force", action="store_true", help="wipe and reload even if seeded")
    args = parser.parse_args(argv)
    seed(force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# 04 — Business Rules & State Machines (LAW)

Every rule below has an ID. Services cite IDs in docstrings; tests cite IDs in names; error messages must be specific and human-readable.

## 1. The 10 mandatory rules

| ID | Rule | Enforcement |
|---|---|---|
| **BR-1** | Vehicle registration number unique (also: driver license number unique) | DB `UNIQUE` + 409 `DUPLICATE_REGISTRATION` / `DUPLICATE_LICENSE` with friendly message |
| **BR-2** | Retired or In-Shop vehicles never appear in dispatch selection | `?dispatchable=true` query filters `status='available'`; service re-checks at create AND dispatch |
| **BR-3** | Drivers with expired license or Suspended status cannot be assigned | `?assignable=true` filter; service re-checks `license_expiry >= today` and `status='available'` at create AND dispatch → `DRIVER_LICENSE_EXPIRED` / `DRIVER_SUSPENDED` |
| **BR-4** | A vehicle/driver already On Trip cannot be assigned to another trip | Service status check + **DB partial unique indexes** `uq_trips_active_vehicle/driver` (race-proof) |
| **BR-5** | Cargo weight ≤ vehicle max load capacity | Service check at create AND dispatch → `CARGO_EXCEEDS_CAPACITY` (message includes both numbers + vehicle name) |
| **BR-6** | Dispatch ⇒ vehicle AND driver → On Trip | `trip_service.dispatch` single transaction, `FOR UPDATE` locks |
| **BR-7** | Complete ⇒ vehicle AND driver → Available (+ vehicle odometer := end_odometer) | `trip_service.complete` |
| **BR-8** | Cancel a dispatched trip ⇒ vehicle AND driver → Available | `trip_service.cancel` |
| **BR-9** | Opening an active maintenance record ⇒ vehicle → In Shop (leaves dispatch pool) | `maintenance_service.create`; vehicle must be `available` first |
| **BR-10** | Closing maintenance ⇒ vehicle → Available **unless retired** | `maintenance_service.close` |

## 2. State machines (only these edges exist)

```
TRIP      draft ──dispatch──▶ dispatched ──complete──▶ completed
            │                     │
            └──cancel──▶ cancelled ◀──cancel──┘        (completed & cancelled are terminal)

VEHICLE   available ──dispatch──▶ on_trip     on_trip ──complete/cancel──▶ available
          available ──open maint──▶ in_shop   in_shop ──close maint──▶ available
          available|in_shop ──retire──▶ retired ──unretire(FM)──▶ available
          (retired blocks: dispatch, maintenance open; closing maint on a retired vehicle keeps retired)

DRIVER    available ──dispatch──▶ on_trip     on_trip ──complete/cancel──▶ available
          available ◀──manual──▶ off_duty     available|off_duty ──suspend──▶ suspended ──reinstate──▶ available
          (on_trip cannot be manually changed; suspend blocked while on_trip → 409 with trip code)
```

Illegal edge ⇒ `409 INVALID_STATUS_TRANSITION`, message pattern: `"Trip TRP-0007 is completed and cannot be dispatched."`

## 3. Transaction recipe (all lifecycle service functions)

```python
def dispatch(db: Session, trip_id: UUID, actor: User) -> Trip:
    """Enforces BR-2..BR-6. One transaction; locks trip→vehicle→driver in that fixed order."""
    trip = db.execute(select(Trip).where(Trip.id == trip_id).with_for_update()).scalar_one_or_none()
    if not trip: raise NotFoundError("trip")
    if trip.status != TripStatus.draft:
        raise DomainError("INVALID_STATUS_TRANSITION", f"Trip {trip.trip_code} is {trip.status.value} and cannot be dispatched.")
    vehicle = db.execute(select(Vehicle).where(Vehicle.id == trip.vehicle_id).with_for_update()).scalar_one()
    driver  = db.execute(select(Driver).where(Driver.id == trip.driver_id).with_for_update()).scalar_one()
    _assert_vehicle_dispatchable(vehicle)   # BR-2, BR-4 → VEHICLE_NOT_AVAILABLE
    _assert_driver_assignable(driver)       # BR-3, BR-4
    _assert_capacity(vehicle, trip.cargo_weight_kg)  # BR-5
    trip.status, trip.dispatched_at, trip.start_odometer = TripStatus.dispatched, now(), vehicle.odometer_km
    vehicle.status = VehicleStatus.on_trip; driver.status = DriverStatus.on_trip   # BR-6
    audit(db, actor, "trip.dispatch", trip)
    db.commit(); db.refresh(trip); return trip
```

The same skeleton applies to `complete` (BR-7: statuses back, odometer forward, optional linked fuel log in same txn), `cancel` (BR-8: restore only if it was dispatched), `maintenance.create/close` (BR-9/10 — lock vehicle row).

## 4. Edge cases the judges will poke (all must return graceful 409/422, never 500)

1. Create trip with a vehicle that is `in_shop` → 409 `VEHICLE_NOT_AVAILABLE` "GJ-01-AB-1234 is in the workshop."
2. Two users dispatch different draft trips for the same vehicle simultaneously → second commit hits `uq_trips_active_vehicle` → catch `IntegrityError` → 409 `VEHICLE_NOT_AVAILABLE` (test with two sessions).
3. Complete with `end_odometer` < `start_odometer` → 409 `END_ODOMETER_LT_START`.
4. Open maintenance on an `on_trip` vehicle → 409 with the active trip code in message.
5. Open second maintenance while one is open → 409 `VEHICLE_HAS_OPEN_MAINTENANCE`.
6. Suspend a driver who is `on_trip` → 409, message names the trip.
7. Driver license expires **while** trip is dispatched → completion still allowed (real world); the driver simply fails `assignable` for the next trip. Document this interpretation.
8. Retire vehicle with open maintenance → close it implicitly? **No** — 409 "Close open maintenance MNT-… first." Keep flows explicit.
9. Cancel a `draft` trip → allowed, no status restore needed (nothing was reserved).
10. Cargo exactly equal to capacity (450 ≤ 500 ✓; 500 ≤ 500 ✓) → allowed; strictly greater blocks.
11. Deleting referenced vehicles/drivers → blocked by FK RESTRICT → UI shows "Retire instead".
12. `fuel_liters` given without `fuel_cost` on completion → 422 both-or-neither.

## 5. Non-mandatory derived rules (still enforce)

- `revenue`, `costs`, `amounts` ≥ 0; `liters`, `cargo`, `distance` > 0 (DB CHECKs mirror Pydantic/zod).
- Email format validated client (zod) + server (Pydantic `EmailStr`) + DB CHECK — three layers, one message style: "Enter a valid email address."
- Trip code format `TRP-` + zero-padded sequence — generated in service, never by client.

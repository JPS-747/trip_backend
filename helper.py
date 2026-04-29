import json
import csv
import os
import random
from datetime import datetime, timedelta
from db_sqlalchemy import get_db, init_db
from models import Client, Vehicle, PublicHoliday, Setting, Trip
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

TRIPS_FILE = "trips.json"
CLIENTS_FILE = "clients.json"
PUBLIC_HOLIDAYS_FILE = "public_holidays.json"

WEEKDAY_RATE = 4.00
SATURDAY_RATE = 5.00
SUNDAY_RATE = 6.00
PUBLIC_HOLIDAY_RATE = 6.50
SETTINGS_STARTING_ODOMETER_KEY = "startingOdometer"


def get_setting(key: str, default=None):
    for db in get_db():
        row = db.query(Setting).filter(Setting.key == key).first()
        if not row:
            return default
        try:
            return json.loads(row.value)
        except json.JSONDecodeError:
            return row.value


def set_setting(key: str, value):
    for db in get_db():
        obj = db.query(Setting).filter(Setting.key == key).first()
        if obj:
            obj.value = json.dumps(value)
        else:
            obj = Setting(key=key, value=json.dumps(value))
            db.add(obj)
        db.commit()


def get_starting_odometer() -> float:
    value = get_setting(SETTINGS_STARTING_ODOMETER_KEY, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def set_starting_odometer(value: float):
    if value < 0:
        raise ValueError("Starting odometer cannot be negative")
    set_setting(SETTINGS_STARTING_ODOMETER_KEY, float(value))


# ---------------------------------------------------------------------------
# Public holidays
# ---------------------------------------------------------------------------


def load_public_holidays() -> dict:
    for db in get_db():
        rows = db.query(PublicHoliday).order_by(PublicHoliday.date).all()
        if not rows:
            return {"holidays": []}
        country = rows[0].country
        year = rows[0].year
        holidays = [{"date": row.date, "name": row.name} for row in rows]
        return {"country": country, "year": year, "holidays": holidays}


def get_holiday_name(date_str: str):
    for db in get_db():
        row = db.query(PublicHoliday).filter(PublicHoliday.date == date_str).first()
        if row:
            return row.name
    return None

def add_holiday(
    date: str, name: str, country: str = "South Africa", year: int = None
) -> dict:
    if year is None:
        try:
            year = datetime.strptime(date, "%Y-%m-%d").year
        except ValueError:
            year = 0
    for db in get_db():
        obj = db.query(PublicHoliday).filter(PublicHoliday.date == date, PublicHoliday.name == name).first()
        if obj:
            obj.country = country
            obj.year = year
        else:
            obj = PublicHoliday(country=country, year=year, date=date, name=name)
            db.add(obj)
        db.commit()
    return {"date": date, "name": name, "country": country, "year": year}


def delete_holiday(date: str, name: str) -> bool:
    for db in get_db():
        obj = db.query(PublicHoliday).filter(PublicHoliday.date == date, PublicHoliday.name == name).first()
        if not obj:
            return False
        db.delete(obj)
        db.commit()
    return True


def import_holidays(holidays: list) -> int:
    """Bulk upsert a list of holiday dicts with keys: date, name, country (opt), year (opt)."""
    count = 0
    for h in holidays:
        if not h.get("date") or not h.get("name"):
            continue
        add_holiday(
            date=h["date"],
            name=h["name"],
            country=h.get("country", "South Africa"),
            year=h.get("year"),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------


def normalize_client_record(row) -> dict:
    d = dict(row)
    return {
        "client": d.get("client", ""),
        "distanceFromOffice": d.get("distanceFromOffice", 0.0),
        "fullAddress": d.get("fullAddress", ""),
        "isDisabled": bool(d.get("isDisabled", 0)),
        "phoneNumber": d.get("phoneNumber", None),
        "email": d.get("email", None),
        "contactPerson": d.get("contactPerson", None),
        "city": d.get("city", None),
    }


def get_client_record(
    client: str,
    distance_from_office: float = 0.0,
    full_address: str = "",
    is_disabled: bool = False,
    phone_number: str = None,
    email: str = None,
    contact_person: str = None,
    city: str = None,
) -> dict:
    return {
        "client": client,
        "distanceFromOffice": distance_from_office,
        "fullAddress": full_address or "",
        "isDisabled": bool(is_disabled),
        "phoneNumber": phone_number,
        "email": email,
        "contactPerson": contact_person,
        "city": city,
    }


def load_clients() -> list:
    for db in get_db():
        rows = db.query(Client).filter(Client.isDisabled == False).order_by(Client.client).all()
        return [
            {
                "client": row.client,
                "distanceFromOffice": row.distanceFromOffice,
                "fullAddress": row.fullAddress,
                "isDisabled": row.isDisabled,
                "phoneNumber": row.phoneNumber,
                "email": row.email,
                "contactPerson": row.contactPerson,
                "city": row.city,
            }
            for row in rows
        ]


def get_client_by_name(client_name: str) -> dict | None:
    """Get a single client record by name (including disabled clients)."""
    for db in get_db():
        client_obj = db.query(Client).filter(Client.client == client_name).first()
        if client_obj:
            # Convert ORM object to dict for normalization
            row = {
                "client": client_obj.client,
                "distanceFromOffice": client_obj.distanceFromOffice,
                "fullAddress": client_obj.fullAddress,
                "isDisabled": client_obj.isDisabled,
                "phoneNumber": client_obj.phoneNumber,
                "email": client_obj.email,
                "contactPerson": client_obj.contactPerson,
                "city": client_obj.city,
            }
            return normalize_client_record(row)
    return None


def upsert_client(
    client: str,
    distance_from_office: float = 0.0,
    full_address: str = None,
    is_disabled: bool | None = None,
    phone_number: str = None,
    email: str = None,
    contact_person: str = None,
    city: str = None,
):
    for db in get_db():
        obj = db.query(Client).filter(Client.client == client).first()
        if obj:
            obj.distanceFromOffice = distance_from_office or obj.distanceFromOffice
            obj.fullAddress = full_address if full_address is not None else obj.fullAddress
            obj.isDisabled = bool(is_disabled) if is_disabled is not None else obj.isDisabled
            obj.phoneNumber = phone_number if phone_number is not None else obj.phoneNumber
            obj.email = email if email is not None else obj.email
            obj.contactPerson = contact_person if contact_person is not None else obj.contactPerson
            obj.city = city if city is not None else obj.city
        else:
            obj = Client(
                client=client,
                distanceFromOffice=distance_from_office,
                fullAddress=full_address or "",
                isDisabled=bool(is_disabled) if is_disabled is not None else False,
                phoneNumber=phone_number,
                email=email,
                contactPerson=contact_person,
                city=city,
            )
            db.add(obj)
        db.commit()


def delete_client(client: str) -> bool:
    """Delete a client by name. Returns True if deleted, False if not found."""
    for db in get_db():
        obj = db.query(Client).filter(Client.client == client).first()
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
    return False


def set_client_disabled(client: str, is_disabled: bool) -> bool:
    for db in get_db():
        obj = db.query(Client).filter(Client.client == client).first()
        if not obj:
            return False
        obj.isDisabled = bool(is_disabled)
        db.commit()
        return True
    return False


def import_clients(clients: list) -> int:
    """Bulk-upsert a list of client dicts. Returns count of records processed."""
    count = 0
    for c in clients:
        if not c.get("client"):
            continue
        upsert_client(
            client=c["client"],
            distance_from_office=c.get("distanceFromOffice", 0.0),
            full_address=c.get("fullAddress", ""),
            is_disabled=c.get("isDisabled"),
            phone_number=c.get("phoneNumber"),
            email=c.get("email"),
            contact_person=c.get("contactPerson"),
            city=c.get("city"),
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# Vehicle management
# ---------------------------------------------------------------------------


def load_vehicles() -> list:
    for db in get_db():
        rows = db.query(Vehicle).filter(Vehicle.isDisabled == False).order_by(Vehicle.regNumber).all()
        return [dict(
            regNumber=row.regNumber,
            make=row.make,
            model=row.model,
            year=row.year,
            kmPerLiter=row.kmPerLiter,
            currentOdometer=row.currentOdometer,
            ratePerKm=row.ratePerKm,
            isDisabled=row.isDisabled
        ) for row in rows]


def get_vehicle(reg_number: str) -> dict | None:
    for db in get_db():
        row = db.query(Vehicle).filter(Vehicle.regNumber == reg_number).first()
        return dict(
            regNumber=row.regNumber,
            make=row.make,
            model=row.model,
            year=row.year,
            kmPerLiter=row.kmPerLiter,
            currentOdometer=row.currentOdometer,
            ratePerKm=row.ratePerKm,
            isDisabled=row.isDisabled
        ) if row else None


def upsert_vehicle(
    reg_number: str,
    make: str = "",
    model: str = "",
    year: int = None,
    km_per_liter: float = 0.0,
    current_odometer: float = None,
    rate_per_km: float = None,
    is_disabled: bool | None = None,
) -> dict:
    for db in get_db():
        obj = db.query(Vehicle).filter(Vehicle.regNumber == reg_number).first()
        if obj:
            obj.make = make or obj.make
            obj.model = model or obj.model
            obj.year = year or obj.year
            obj.kmPerLiter = km_per_liter or obj.kmPerLiter
            obj.currentOdometer = current_odometer if current_odometer is not None else obj.currentOdometer
            obj.ratePerKm = rate_per_km if rate_per_km is not None else obj.ratePerKm
            obj.isDisabled = bool(is_disabled) if is_disabled is not None else obj.isDisabled
        else:
            obj = Vehicle(
                regNumber=reg_number,
                make=make or "",
                model=model or "",
                year=year,
                kmPerLiter=km_per_liter or 0.0,
                currentOdometer=current_odometer or 0.0,
                ratePerKm=rate_per_km or 0.0,
                isDisabled=bool(is_disabled) if is_disabled is not None else False
            )
            db.add(obj)
        db.commit()
        return get_vehicle(reg_number) or {}


def delete_vehicle(reg_number: str) -> bool:
    for db in get_db():
        obj = db.query(Vehicle).filter(Vehicle.regNumber == reg_number).first()
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True


def set_vehicle_disabled(reg_number: str, is_disabled: bool) -> bool:
    for db in get_db():
        obj = db.query(Vehicle).filter(Vehicle.regNumber == reg_number).first()
        if not obj:
            return False
        obj.isDisabled = bool(is_disabled)
        db.commit()
        return True



def normalize_trip_record(trip) -> dict:
    d = dict(trip)
    built = {
        "date": d["date"],
        "client": d["client"],
        "city": d["city"],
        "distanceKm": d.get("distanceKm", d.get("distanceKm", 0.0)),
        "totalDistanceKm": d.get("totalDistanceKm", d.get("totalDistanceKm", 0.0)),
        "tripType": d.get("tripType", d.get("tripType", 1)),
        "isPrivateTrip": bool(d.get("isPrivateTrip", 0)),
        "vehicleRegNumber": d.get("vehicleRegNumber"),
    }
    built["id"] = d.get("id")

    # Get client city if it's not a private trip
    if not built["isPrivateTrip"]:
        client_info = get_client_by_name(d["client"])
        if client_info:
            built["clientCity"] = client_info.get("city")
        else:
            built["clientCity"] = None
    else:
        built["clientCity"] = None

    # Add computed fields (day type, rate, amount)
    date_obj = datetime.strptime(d["date"], "%Y-%m-%d")
    built["isWeekday"] = date_obj.weekday() < 5  # Monday-Friday
    built["isSaturday"] = date_obj.weekday() == 5
    built["isSunday"] = date_obj.weekday() == 6

    # Check if it's a public holiday
    holiday_name = get_holiday_name(d["date"])
    built["isPublicHoliday"] = bool(holiday_name)
    built["publicHolidayName"] = holiday_name

    # Determine rate type and per-km rate
    if built["isPublicHoliday"]:
        built["rateType"] = "Public Holiday"
        built["ratePerKm"] = PUBLIC_HOLIDAY_RATE
    elif built["isSunday"]:
        built["rateType"] = "Sunday"
        built["ratePerKm"] = SUNDAY_RATE
    elif built["isSaturday"]:
        built["rateType"] = "Saturday"
        built["ratePerKm"] = SATURDAY_RATE
    else:  # Weekday
        built["rateType"] = "Weekday"
        built["ratePerKm"] = WEEKDAY_RATE

    # Calculate total amount
    built["totalAmount"] = round(
        built.get("totalDistanceKm", 0) * built.get("ratePerKm", 0), 2
    )

    return built



def load_raw_trips() -> list:
    for db in get_db():
        rows = db.query(Trip).order_by(Trip.date, Trip.id).all()
        return [dict(
            id=row.id,
            date=row.date,
            client=row.client,
            city=row.city,
            distanceKm=row.distanceKm,
            totalDistanceKm=row.totalDistanceKm,
            tripType=row.tripType,
            isPrivateTrip=row.isPrivateTrip,
            vehicleRegNumber=row.vehicleRegNumber
        ) for row in rows]


def load_trips() -> list:
    trips = [normalize_trip_record(trip) for trip in load_raw_trips()]
    return apply_odometer_readings(trips)


def apply_odometer_readings(trips: list, start_reading: float = None) -> list:
    """
    Apply odometer readings to trips.
    For vehicle-assigned trips: Use vehicle's currentOdometer from DB and work backwards.
    For unassigned trips: use the global starting odometer and count forward.
    """
    # Group trips by vehicle
    vehicle_trips = {}
    unassigned_trips = []

    for trip in trips:
        vehicle_reg = trip.get("vehicleRegNumber")
        if vehicle_reg:
            if vehicle_reg not in vehicle_trips:
                vehicle_trips[vehicle_reg] = []
            vehicle_trips[vehicle_reg].append(trip)
        else:
            unassigned_trips.append(trip)

    # Process vehicle-assigned trips - use vehicle's currentOdometer and work backwards
    for vehicle_reg, vtrips in vehicle_trips.items():
        vehicle = get_vehicle(vehicle_reg)
        if not vehicle:
            continue

        # Get the vehicle's current odometer (this is the final odometer after all trips)
        final_odometer = vehicle.get("currentOdometer", 0.0) or 0.0

        # Calculate total distance for all trips of this vehicle
        total_distance = sum(t.get("totalDistanceKm", 0) or 0 for t in vtrips)

        # Starting odometer is final_odometer minus total distance
        starting_odometer = final_odometer - total_distance

        # Now apply odometer readings going forward
        current = starting_odometer
        for trip in vtrips:
            trip["odometerStart"] = round(current, 2)
            current += trip.get("totalDistanceKm", 0) or 0
            trip["odometerEnd"] = round(current, 2)

    # Process unassigned trips (use global starting odometer)
    global_starting = (
        start_reading if start_reading is not None else get_starting_odometer()
    )
    current = global_starting
    for trip in unassigned_trips:
        trip["odometerStart"] = round(current, 2)
        current += trip.get("totalDistanceKm", 0) or 0
        trip["odometerEnd"] = round(current, 2)

    return trips


def _insert_trip_db(trip: dict) -> int:
    for db in get_db():
        trip_obj = Trip(
            date=trip["date"],
            client=trip["client"],
            city=trip["city"],
            distanceKm=trip["distanceKm"],
            totalDistanceKm=trip["totalDistanceKm"],
            tripType=trip["tripType"],
            isPrivateTrip=int(trip.get("isPrivateTrip", 0)),
            vehicleRegNumber=trip.get("vehicleRegNumber"),
        )
        db.add(trip_obj)
        db.commit()
        db.refresh(trip_obj)
        return trip_obj.id


def _insert_trip_db_with_odometer_update(trip: dict) -> int:
    """Inserts a trip and update vehicle odometer if a vehicle is associated."""
    trip_id = _insert_trip_db(trip)

    # Update vehicle's odometer if a vehicle is associated with this trip
    vehicle_reg_number = trip.get("vehicleRegNumber")
    if vehicle_reg_number:
        vehicle = get_vehicle(vehicle_reg_number)
        if vehicle:
            current_odo = vehicle.get("currentOdometer", 0.0) or 0.0
            total_distance_km = trip.get("totalDistanceKm", 0) or 0
            new_odo = current_odo + total_distance_km
            upsert_vehicle(vehicle_reg_number, current_odometer=new_odo)

    return trip_id


def save_trips(trips: list):
    """Replace all trips in the DB with the given list."""
    for db in get_db():
        db.execute("DELETE FROM trips")
    for trip in trips:
        _insert_trip_db(trip)


def get_trip(trip_id: int) -> dict | None:
    for db in get_db():
        trip_obj = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip_obj:
            return None
        # Convert ORM object to dict for normalization
        trip_dict = {
            "id": trip_obj.id,
            "date": trip_obj.date,
            "client": trip_obj.client,
            "city": trip_obj.city,
            "distanceKm": trip_obj.distanceKm,
            "totalDistanceKm": trip_obj.totalDistanceKm,
            "tripType": trip_obj.tripType,
            "isPrivateTrip": trip_obj.isPrivateTrip,
            "vehicleRegNumber": trip_obj.vehicleRegNumber,
        }
        trip = normalize_trip_record(trip_dict)

        vehicle_reg = trip.get("vehicleRegNumber")

        if vehicle_reg:
            # Load all trips for this vehicle, sorted by date and ID to get correct sequence
            vehicle_trips = db.query(Trip).filter(Trip.vehicleRegNumber == vehicle_reg).order_by(Trip.date, Trip.id).all()
            vehicle_trips = [normalize_trip_record({
                "id": t.id,
                "date": t.date,
                "client": t.client,
                "city": t.city,
                "distanceKm": t.distanceKm,
                "totalDistanceKm": t.totalDistanceKm,
                "tripType": t.tripType,
                "isPrivateTrip": t.isPrivateTrip,
                "vehicleRegNumber": t.vehicleRegNumber,
            }) for t in vehicle_trips]

            # Get vehicle's current odometer from DB
            vehicle = db.query(Vehicle).filter(Vehicle.regNumber == vehicle_reg).first()
            if vehicle:
                final_odometer = vehicle.currentOdometer or 0.0
                total_distance = sum(t.get("totalDistanceKm", 0) or 0 for t in vehicle_trips)
                starting_odometer = final_odometer - total_distance

                # Apply odometer readings going forward
                current = starting_odometer
                for vtrip in vehicle_trips:
                    vtrip["odometerStart"] = round(current, 2)
                    current += vtrip.get("totalDistanceKm", 0) or 0
                    vtrip["odometerEnd"] = round(current, 2)
                    if vtrip.get("id") == trip.get("id"):
                        trip = vtrip
                        break
        else:
            # No vehicle assigned, use global odometer calculation
            start_reading = get_starting_odometer()
            all_unassigned = db.query(Trip).filter(Trip.vehicleRegNumber == None).order_by(Trip.date, Trip.id).all()
            all_unassigned = [normalize_trip_record({
                "id": t.id,
                "date": t.date,
                "client": t.client,
                "city": t.city,
                "distanceKm": t.distanceKm,
                "totalDistanceKm": t.totalDistanceKm,
                "tripType": t.tripType,
                "isPrivateTrip": t.isPrivateTrip,
                "vehicleRegNumber": t.vehicleRegNumber,
            }) for t in all_unassigned]

            current = start_reading
            for utrip in all_unassigned:
                utrip["odometerStart"] = round(current, 2)
                current += utrip.get("totalDistanceKm", 0) or 0
                utrip["odometerEnd"] = round(current, 2)
                if utrip.get("id") == trip.get("id"):
                    trip = utrip
                    break

        return trip
def create_trip_record(
    *,
    date: str,
    client: str,
    city: str,
    distance_km: float,
    trip_type: int,
    total_distance_km: float,
    is_private_trip: bool = False,
    vehicle_reg_number: str | None = None,
) -> dict:
    trip = build_trip(
        date,
        client,
        city,
        distance_km,
        trip_type,
        is_private_trip,
        vehicle_reg_number,
    )
    # Override the calculated totalDistanceKm with the provided value
    trip["totalDistanceKm"] = round(total_distance_km, 1)
    # Recalculate totalAmount based on the new total distance
    trip["totalAmount"] = round(trip["totalDistanceKm"] * trip["ratePerKm"], 2)
    new_id = _insert_trip_db(trip)
    created = get_trip(new_id)

    # Update vehicle's odometer if a vehicle is associated with this trip
    if vehicle_reg_number:
        # Get current vehicle odometer from DB
        vehicle = get_vehicle(vehicle_reg_number)
        if vehicle:
            current_odo = vehicle.get("currentOdometer", 0.0) or 0.0
            # Add the trip distance to the current odometer
            new_odo = current_odo + total_distance_km
            # Update vehicle's odometer in DB
            upsert_vehicle(vehicle_reg_number, current_odometer=new_odo)

    return created or trip


def update_trip_record(
    trip_id: int,
    *,
    date: str,
    client: str,
    city: str,
    distance_km: float,
    trip_type: int,
    total_distance_km: float,
    is_private_trip: bool = False,
    vehicle_reg_number: str | None = None,
) -> dict | None:
    existing = get_trip(trip_id)
    if not existing:
        return None

    # Track the old vehicle in case it changed
    old_vehicle_reg = existing.get("vehicleRegNumber")

    trip = build_trip(
        date, client, city, distance_km, trip_type, is_private_trip, vehicle_reg_number
    )
    # Override the calculated totalDistanceKm with the provided value
    trip["totalDistanceKm"] = round(total_distance_km, 1)
    # Recalculate totalAmount based on the new total distance
    trip["totalAmount"] = round(trip["totalDistanceKm"] * trip["ratePerKm"], 2)
    for db in get_db():
        result = db.execute(
            """
            UPDATE trips
               SET date=?, client=?, city=?, distanceKm=?, tripType=?, totalDistanceKm=?, isPrivateTrip=?, vehicleRegNumber=?
             WHERE id=?
            """,
            (
                trip["date"],
                trip["client"],
                trip["city"],
                trip["distanceKm"],
                trip["tripType"],
                trip["totalDistanceKm"],
                int(trip.get("isPrivateTrip", 0)),
                trip.get("vehicleRegNumber"),
                trip_id,
            ),
        )
        if result.rowcount == 0:
            return None

    # Update odometers for affected vehicles
    # If the vehicle changed, update both the old and new vehicle
    if old_vehicle_reg and old_vehicle_reg != vehicle_reg_number:
        # Subtract old trip distance from old vehicle
        old_trip_distance = existing.get("totalDistanceKm", 0)
        old_vehicle = get_vehicle(old_vehicle_reg)
        if old_vehicle:
            old_odo = old_vehicle.get("currentOdometer", 0.0) or 0.0
            new_old_odo = old_odo - old_trip_distance
            upsert_vehicle(old_vehicle_reg, current_odometer=new_old_odo)

    if vehicle_reg_number:
        # Calculate the distance change for new vehicle
        new_trip_distance = trip["totalDistanceKm"]
        old_trip_distance = existing.get("totalDistanceKm", 0)
        distance_delta = new_trip_distance - old_trip_distance

        new_vehicle = get_vehicle(vehicle_reg_number)
        if new_vehicle:
            new_odo = new_vehicle.get("currentOdometer", 0.0) or 0.0
            updated_odo = new_odo + distance_delta
            upsert_vehicle(vehicle_reg_number, current_odometer=updated_odo)

    return get_trip(trip_id)


def delete_trip_record(trip_id: int) -> bool:
    # Fetch the trip before deleting it to get vehicle info and distance
    trip = get_trip(trip_id)
    vehicle_reg_number = trip.get("vehicleRegNumber") if trip else None
    trip_distance = trip.get("totalDistanceKm", 0) if trip else 0

    for db in get_db():
        result = db.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        deleted = result.rowcount > 0

    # Update vehicle's odometer if the trip had a vehicle
    if deleted and vehicle_reg_number:
        vehicle = get_vehicle(vehicle_reg_number)
        if vehicle:
            current_odo = vehicle.get("currentOdometer", 0.0) or 0.0
            # Subtract the trip distance from the vehicle's odometer
            new_odo = current_odo - trip_distance
            upsert_vehicle(vehicle_reg_number, current_odometer=new_odo)

    return deleted


def cleanup_trips_data() -> list:
    cleaned = [normalize_trip_record(t) for t in load_raw_trips()]
    save_trips(cleaned)
    return cleaned


def clear_trips_data(start_date: str | None = None, end_date: str | None = None) -> int:
    for db in get_db():
        # First, fetch all trips that will be deleted to update vehicle odometers
        if start_date or end_date:
            q = db.query(Trip)
            if start_date:
                q = q.filter(Trip.date >= start_date)
            if end_date:
                q = q.filter(Trip.date <= end_date)
            trips_to_delete = q.all()
        else:
            trips_to_delete = db.query(Trip).all()

    # Deduct distances from vehicle odometers
    vehicle_distance_map = {}  # Map vehicle reg -> total distance to deduct
    for trip in trips_to_delete:
        vehicle_reg = trip.vehicleRegNumber
        if vehicle_reg:
            total_distance = trip.totalDistanceKm or 0
            vehicle_distance_map[vehicle_reg] = (
                vehicle_distance_map.get(vehicle_reg, 0) + total_distance
            )

    # Update each vehicle's odometer
    for vehicle_reg, total_distance in vehicle_distance_map.items():
        vehicle = get_vehicle(vehicle_reg)
        if vehicle:
            current_odo = vehicle.get("currentOdometer", 0.0) or 0.0
            new_odo = max(
                0.0, current_odo - total_distance
            )  # Ensure odometer doesn't go below 0
            upsert_vehicle(vehicle_reg, current_odometer=new_odo)

    # Now delete the trips
    for db in get_db():
        if start_date or end_date:
            q = db.query(Trip)
            if start_date:
                q = q.filter(Trip.date >= start_date)
            if end_date:
                q = q.filter(Trip.date <= end_date)
            trip_count = q.delete(synchronize_session=False)
            db.commit()
            print(f"DEBUG: Deleted {trip_count} trips")
        else:
            print(f"DEBUG: Clearing all trips")
            trip_count = db.query(Trip).delete(synchronize_session=False)
            db.commit()
    return trip_count


def clear_clients_data() -> list:
    for db in get_db():
        db.execute("DELETE FROM clients")
    return []


def clear_holidays_data() -> list:
    for db in get_db():
        db.execute("DELETE FROM public_holidays")
    return []


# ---------------------------------------------------------------------------
# Filters, sorting, pagination
# ---------------------------------------------------------------------------


def filter_sort_paginate_trips(
    page=1,
    page_size=10,
    client=None,
    day_type=None,
    sort_by="date",
    sort_order="asc",
) -> dict:
    trips = load_trips()

    if client:
        trips = [t for t in trips if t["client"].lower() == client.lower()]

    if day_type:
        normalized = day_type.lower()
        day_type_checks = {
            "weekday": lambda t: t["isWeekday"],
            "saturday": lambda t: t["isSaturday"],
            "sunday": lambda t: t["isSunday"],
            "publicholiday": lambda t: t["isPublicHoliday"],
        }
        if normalized in day_type_checks:
            trips = [t for t in trips if day_type_checks[normalized](t)]

    reverse = sort_order.lower() == "desc"
    sort_key_map = {
        "date": lambda t: t["date"],
        "client": lambda t: t["client"].lower(),
        "city": lambda t: t.get("city", "").lower(),
        "distancekm": lambda t: t["distanceKm"],
        "totaldistancekm": lambda t: t["totalDistanceKm"],
        "isprivatetrip": lambda t: t["isPrivateTrip"],
    }
    sort_key = sort_key_map.get(sort_by.lower(), sort_key_map["date"])
    trips = sorted(trips, key=sort_key, reverse=reverse)

    total_items = len(trips)
    total_distance_km = sum(t.get("totalDistanceKm", 0) or 0 for t in trips)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start_index = (page - 1) * page_size
    items = trips[start_index : start_index + page_size]

    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "totalItems": total_items,
        "totalPages": total_pages,
        "totalDistanceKm": round(total_distance_km, 2),
    }


def filter_sort_paginate_clients(
    page=1,
    page_size=10,
    sort_by="client",
    sort_order="asc",
) -> dict:
    clients = load_clients()

    reverse = sort_order.lower() == "desc"
    sort_key_map = {
        "client": lambda c: c["client"].lower(),
        "city": lambda c: c["city"].lower(),
        "distancefromoffice": lambda c: c["distanceFromOffice"],
    }
    sort_key = sort_key_map.get(sort_by.lower(), sort_key_map["client"])
    clients = sorted(clients, key=sort_key, reverse=reverse)

    total_items = len(clients)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start_index = (page - 1) * page_size
    items = clients[start_index : start_index + page_size]

    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "totalItems": total_items,
        "totalPages": total_pages,
    }


# ---------------------------------------------------------------------------
# Add a single trip
# ---------------------------------------------------------------------------


def add_trip(
    date: str,
    client: str,
    city: str,
    distance_km: float,
    trip_type: int,
    is_private_trip: bool = False,
):
    trip = build_trip(date, client, city, distance_km, trip_type, is_private_trip)
    _insert_trip_db(trip)
    upsert_client(client, distance_from_office=distance_km)
    return trip


# ---------------------------------------------------------------------------
# Sample data generation
# ---------------------------------------------------------------------------


def generate_sample_trips(
    number_of_entries, use_date, isPrivate, selected_vehicles=None
) -> list:
    """
    Generate sample trips for a given date with the following rules:
    - If multiple vehicles selected: randomize which vehicle gets each trip
    - City-weighted client selection: probability based on number of clients per city
    - Max 1 return trip (trip_type=2) per day, must be the first trip
    - Additional trips (if any): same city as the first trip, one-way (trip_type=1)
    - For private trips: use random distance, no city-based logic applies
    """
    generated = []
    date_str = use_date.strftime("%Y-%m-%d")

    if number_of_entries <= 0:
        return generated

    # Get available clients (excluding disabled ones)
    available_clients = load_clients() if not isPrivate else []

    if isPrivate:
        # For private trips: generate number_of_entries random distance trips
        for _ in range(number_of_entries):
            vehicle_reg_number = None
            if selected_vehicles and len(selected_vehicles) > 0:
                vehicle_reg_number = random.choice(selected_vehicles)

            distance = round(random.uniform(3.0, 10.0), 1)
            generated.append(
                {
                    "date": date_str,
                    "client": "Private Trip",
                    "city": "N/A",
                    "distanceKm": distance,
                    "totalDistanceKm": distance * 1,  # Private trips are always one-way
                    "tripType": 1,
                    "isPrivateTrip": True,
                    "vehicleRegNumber": vehicle_reg_number,
                }
            )
    else:
        # For regular trips: apply city-weighted selection and trip-type rules
        if not available_clients:
            return generated

        # Calculate client distribution by city (for weighting)
        city_counts = {}
        for client in available_clients:
            city = client.get("city") or "Unassigned"
            city_counts[city] = city_counts.get(city, 0) + 1

        # Selected primary client (first trip of the day)
        # Weight selection by number of clients in each city
        primary_client = random.choice(available_clients)
        primary_city = primary_client.get("city") or "Unassigned"

        # First trip: can be return (trip_type=2) or one-way (trip_type=1)
        # Probability of return trip: 60% if distance < 30km, 40% if >= 30km
        distance_km = primary_client.get("distanceFromOffice", 0) or 0
        is_return_trip = (
            random.random() < 0.6 if distance_km < 30 else random.random() < 0.4
        )
        trip_type_1 = 2 if is_return_trip else 1

        vehicle_reg_number_1 = None
        if selected_vehicles and len(selected_vehicles) > 0:
            vehicle_reg_number_1 = random.choice(selected_vehicles)

        generated.append(
            {
                "date": date_str,
                "client": primary_client.get("client"),
                "city": primary_city,
                "distanceKm": distance_km,
                "totalDistanceKm": distance_km * trip_type_1,
                "tripType": trip_type_1,
                "isPrivateTrip": False,
                "vehicleRegNumber": vehicle_reg_number_1,
            }
        )

        # Additional trips (if any): same city, all one-way (trip_type=1)
        if number_of_entries > 1:
            # Find all clients from the same city as the primary client
            same_city_clients = [
                c
                for c in available_clients
                if (c.get("city") or "Unassigned") == primary_city
            ]

            for i in range(1, number_of_entries):
                if same_city_clients:
                    additional_client = random.choice(same_city_clients)
                    additional_distance = random.randint(2, 10)

                    generated.append(
                        {
                            "date": date_str,
                            "client": additional_client.get("client"),
                            "city": primary_city,
                            "distanceKm": additional_distance,
                            "totalDistanceKm": additional_distance
                            * 1,  # Always one-way
                            "tripType": 1,
                            "isPrivateTrip": False,
                            "vehicleRegNumber": vehicle_reg_number_1,
                        }
                    )

    return generated


def weekdays_in_range(start_date, end_date):
    day_count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0=Monday, 6=Sunday
            day_count += 1
        current += timedelta(days=1)
    return day_count


def saturdays_in_range(start_date, end_date):
    day_count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() == 5:  # 0=Monday, 6=Sunday
            day_count += 1
        current += timedelta(days=1)
    return day_count


def sundays_in_range(start_date, end_date):
    day_count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() == 6:  # 0=Monday, 6=Sunday
            day_count += 1
        current += timedelta(days=1)
    return day_count


def holidays_in_range(start_date, end_date) -> list:
    """Retrieve all holidays from the database within the given date range."""
    start_str = (
        start_date.strftime("%Y-%m-%d")
        if hasattr(start_date, "strftime")
        else start_date
    )
    end_str = (
        end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else end_date
    )

    for db in get_db():
        rows = (
            db.query(PublicHoliday)
            .filter(PublicHoliday.date >= start_str, PublicHoliday.date <= end_str)
            .order_by(PublicHoliday.date)
            .all()
        )
        return [{"date": row.date, "name": row.name} for row in rows]


def is_public_holiday(date_str: str) -> bool:
    """Check if a given date is a public holiday using SQLAlchemy ORM."""
    for db in get_db():
        row = db.query(PublicHoliday).filter(PublicHoliday.date == date_str).first()
        return row is not None


def get_seasonal_multiplier(
    date: datetime, peak_month: float = 5.5, spread: float = 1.8
) -> float:
    """
    Calculate a seasonal multiplier that peaks in mid-year (Aug-Sept in financial year).
    Financial year: March 1 - Feb 28/29
    Month 0=Mar, Month 5=Aug, Month 6=Sept (peak), Month 11=Feb (low)

    Args:
        date: The date to calculate the multiplier for
        peak_month: Financial year month where peak occurs (0-11, default 5.5 for Aug-Sept)
        spread: Standard deviation in months (default 1.8 for steep falloff)

    Returns a multiplier between 0.5 (low) and 1.5 (peak).
    Bell curve peaking at peak_month with configurable spread.
    """
    import math

    month = date.month - 1  # Convert to 0-11 (Jan=0, Dec=11)

    # Convert calendar month to financial year month (0=Mar, 11=Feb)
    financial_month = (month - 2) % 12

    # Bell curve centered at peak_month
    # Peak multiplier: 1.5
    # Low multiplier: 0.5
    # Spread: standard deviation in months for controlling falloff steepness
    distance_from_peak = financial_month - peak_month
    exponent = -(distance_from_peak**2) / (2 * spread**2)
    multiplier = 1.0 + 0.5 * math.exp(exponent)

    # Clamp to ensure we stay in reasonable range
    return max(0.5, min(1.5, multiplier))


def emit_progress(step: str, details: dict = None, progress_callback=None):
    """Emit progress update via callback."""
    if progress_callback:
        try:
            progress_callback(step, details or {})
        except Exception as e:
            print(f"[emit_progress] Error emitting progress: {e}")
    print(f"[emit_progress] {step}: {details or {}}")


def add_sample_data(
    start_date=None,
    end_date=None,
    start_odometer_reading=None,
    weekday_min_trips_per_day=0,
    weekday_max_trips_per_day=0,
    weekday_avg_distance_per_month=None,
    saturday_min_trips_per_day=0,
    saturday_max_trips_per_day=2,
    saturday_avg_distance_per_month=None,
    sunday_min_trips_per_day=0,
    sunday_max_trips_per_day=1,
    sunday_avg_distance_per_month=None,
    holiday_min_trips_per_day=0,
    holiday_max_trips_per_day=3,
    holiday_avg_distance_per_month=None,
    use_seasonal_multiplier=True,
    seasonal_peak_month=5.5,
    seasonal_spread=1.8,
    selected_vehicles=None,
    progress_callback=None,
):
    """
    Generate and seed sample trips with smart distance management.

    For each day type and month, if the total distance falls outside 10% of the target
    average distance, the function will:
    - Add random trips on random days (if below target)
    - Remove random trips on random days (if above target)


    """

    start_date_value = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_value = datetime.strptime(end_date, "%Y-%m-%d")

    emit_progress(
        "initialized",
        {
            "startDate": start_date,
            "endDate": end_date,
            "selectedVehicles": selected_vehicles,
        },
    )

    # Collect all trips by day type and month
    all_trips = []
    weekday_trips_by_month = {}  # {(year, month): [trips]}
    saturday_trips_by_month = {}
    sunday_trips_by_month = {}
    holiday_trips_by_month = {}

    # Generate weekday trips
    if weekday_max_trips_per_day > 0:
        days_in_range = weekdays_in_range(start_date_value, end_date_value)
        avg_trips_per_day = int(
            (weekday_min_trips_per_day + weekday_max_trips_per_day) / 2
        )
        emit_progress(
            "generating_weekday_trips",
            {"daysInRange": days_in_range, "avgTripsPerDay": avg_trips_per_day},
        )

        current = start_date_value
        while current <= end_date_value:
            if current.weekday() < 5:  # Monday–Friday only
                date_str = current.strftime("%Y-%m-%d")
                # Skip if this day is a public holiday
                if is_public_holiday(date_str):
                    current += timedelta(days=1)
                    continue

                # Apply seasonal multiplier
                seasonal_multiplier = (
                    get_seasonal_multiplier(
                        current, seasonal_peak_month, seasonal_spread
                    )
                    if use_seasonal_multiplier
                    else 1.0
                )
                adjusted_min = max(
                    0, int(weekday_min_trips_per_day * seasonal_multiplier)
                )
                adjusted_max = max(
                    1, int(weekday_max_trips_per_day * seasonal_multiplier)
                )

                number_of_entries = random.randint(adjusted_min, adjusted_max)
                gen_trips = generate_sample_trips(
                    number_of_entries, current, False, selected_vehicles
                )

                # Collect by month
                month_key = (current.year, current.month)
                if month_key not in weekday_trips_by_month:
                    weekday_trips_by_month[month_key] = []
                weekday_trips_by_month[month_key].extend(gen_trips)

            current += timedelta(days=1)

        emit_progress(
            "weekday_trips_generated",
            {
                "totalTrips": sum(
                    len(trips) for trips in weekday_trips_by_month.values()
                )
            },
        )

    # Generate Saturday trips
    if saturday_max_trips_per_day > 0:
        days_in_range = saturdays_in_range(start_date_value, end_date_value)
        avg_trips_per_day = int(
            (saturday_min_trips_per_day + saturday_max_trips_per_day) / 2
        )
        emit_progress(
            "generating_saturday_trips",
            {"daysInRange": days_in_range, "avgTripsPerDay": avg_trips_per_day},
        )
        print(
            f"Generating sample Saturday trips: {days_in_range} days, avg {avg_trips_per_day} trips/day (with seasonal variation)"
        )
        current = start_date_value
        while current <= end_date_value:
            if current.weekday() == 5:  # Saturday only
                date_str = current.strftime("%Y-%m-%d")
                # Skip if this Saturday is a public holiday
                if is_public_holiday(date_str):
                    current += timedelta(days=1)
                    continue

                # Apply seasonal multiplier
                seasonal_multiplier = (
                    get_seasonal_multiplier(
                        current, seasonal_peak_month, seasonal_spread
                    )
                    if use_seasonal_multiplier
                    else 1.0
                )
                adjusted_min = max(
                    0, int(saturday_min_trips_per_day * seasonal_multiplier)
                )
                adjusted_max = max(
                    1, int(saturday_max_trips_per_day * seasonal_multiplier)
                )

                number_of_entries = random.randint(adjusted_min, adjusted_max)
                gen_trips = generate_sample_trips(
                    number_of_entries, current, True, selected_vehicles
                )

                # Collect by month
                month_key = (current.year, current.month)
                if month_key not in saturday_trips_by_month:
                    saturday_trips_by_month[month_key] = []
                saturday_trips_by_month[month_key].extend(gen_trips)

            current += timedelta(days=1)

        emit_progress(
            "saturday_trips_generated",
            {
                "totalTrips": sum(
                    len(trips) for trips in saturday_trips_by_month.values()
                )
            },
        )

    # Generate Sunday trips
    if sunday_max_trips_per_day > 0:
        days_in_range = sundays_in_range(start_date_value, end_date_value)
        avg_trips_per_day = int(
            (sunday_min_trips_per_day + sunday_max_trips_per_day) / 2
        )
        emit_progress(
            "generating_sunday_trips",
            {"daysInRange": days_in_range, "avgTripsPerDay": avg_trips_per_day},
        )
        print(
            f"Generating sample Sunday trips: {days_in_range} days, avg {avg_trips_per_day} trips/day (with seasonal variation)"
        )
        current = start_date_value
        while current <= end_date_value:
            if current.weekday() == 6:  # Sunday only
                date_str = current.strftime("%Y-%m-%d")
                # Skip if this Sunday is a public holiday
                if is_public_holiday(date_str):
                    current += timedelta(days=1)
                    continue

                # Apply seasonal multiplier
                seasonal_multiplier = (
                    get_seasonal_multiplier(
                        current, seasonal_peak_month, seasonal_spread
                    )
                    if use_seasonal_multiplier
                    else 1.0
                )
                adjusted_min = max(
                    0, int(sunday_min_trips_per_day * seasonal_multiplier)
                )
                adjusted_max = max(
                    1, int(sunday_max_trips_per_day * seasonal_multiplier)
                )

                number_of_entries = random.randint(adjusted_min, adjusted_max)
                gen_trips = generate_sample_trips(
                    number_of_entries, current, True, selected_vehicles
                )

                # Collect by month
                month_key = (current.year, current.month)
                if month_key not in sunday_trips_by_month:
                    sunday_trips_by_month[month_key] = []
                sunday_trips_by_month[month_key].extend(gen_trips)

            current += timedelta(days=1)

        emit_progress(
            "sunday_trips_generated",
            {"totalTrips": sum(len(trips) for trips in sunday_trips_by_month.values())},
        )

    # Generate holiday trips
    if holiday_max_trips_per_day > 0:
        holidays = holidays_in_range(start_date, end_date)
        if len(holidays) > 0:
            emit_progress(
                "generating_holiday_trips",
                {
                    "holidayCount": len(holidays),
                    "avgTripsPerHoliday": (
                        holiday_min_trips_per_day + holiday_max_trips_per_day
                    )
                    / 2,
                },
            )
            print(
                f"Generating sample public holiday trips: {len(holidays)} holidays, avg {(holiday_min_trips_per_day + holiday_max_trips_per_day) / 2} trips/holiday (with seasonal variation)"
            )
            for h in holidays:
                date_obj = datetime.strptime(h["date"], "%Y-%m-%d")

                # Apply seasonal multiplier
                seasonal_multiplier = (
                    get_seasonal_multiplier(
                        date_obj, seasonal_peak_month, seasonal_spread
                    )
                    if use_seasonal_multiplier
                    else 1.0
                )
                adjusted_min = max(
                    0, int(holiday_min_trips_per_day * seasonal_multiplier)
                )
                adjusted_max = max(
                    1, int(holiday_max_trips_per_day * seasonal_multiplier)
                )

                number_of_entries = random.randint(adjusted_min, adjusted_max)
                gen_trips = generate_sample_trips(
                    number_of_entries, date_obj, True, selected_vehicles
                )

                # Collect by month
                month_key = (date_obj.year, date_obj.month)
                if month_key not in holiday_trips_by_month:
                    holiday_trips_by_month[month_key] = []
                holiday_trips_by_month[month_key].extend(gen_trips)

        emit_progress(
            "holiday_trips_generated",
            {
                "totalTrips": sum(
                    len(trips) for trips in holiday_trips_by_month.values()
                )
            },
        )

    # Helper function to adjust trips to target distance with 10% tolerance
    def adjust_trips_to_target(trips, target_distance, day_type_name, month_key):
        if not target_distance or not trips:
            return trips

        # Filter trips to only include those matching the day_type_name
        day_type_lower = day_type_name.lower()
        filtered_trips = []
        for t in trips:
            trip_date = datetime.strptime(t.get("date"), "%Y-%m-%d")
            is_weekday = trip_date.weekday() < 5
            is_saturday = trip_date.weekday() == 5
            is_sunday = trip_date.weekday() == 6
            is_holiday = is_public_holiday(trip_date.strftime("%Y-%m-%d"))
            
            # Only include trips matching the day type
            if day_type_lower == "weekday" and is_weekday:
                filtered_trips.append(t)
            elif day_type_lower == "saturday" and is_saturday:
                filtered_trips.append(t)
            elif day_type_lower == "sunday" and is_sunday:
                filtered_trips.append(t)
            elif day_type_lower == "holiday" and is_holiday:
                filtered_trips.append(t)
        
        total_distance = sum(t.get("totalDistanceKm", 0) or 0 for t in filtered_trips)
        lower_bound = target_distance * 0.9  # 10% below target
        upper_bound = target_distance * 1.1  # 10% above target

        emit_progress(
            f"adjusting_{day_type_name.lower()}_distance",
            {
                "dayType": day_type_name,
                "month": month_key,
                "target": target_distance,
                "current": total_distance,
                "lowerBound": lower_bound,
                "upperBound": upper_bound,
            },
            progress_callback,
        )

        if total_distance < lower_bound:
            # Need to add trips
            distance_needed = lower_bound - total_distance

            while total_distance < lower_bound and len(trips) < 1000:  # Safety limit
                # Generate a random trip for a random date in this month
                year, month = month_key
                day = random.randint(1, 28)  # Safe day for all months
                try:
                    random_date = datetime(year, month, day)
                    
                    # Determine if this day matches the day_type_name
                    is_weekday = random_date.weekday() < 5
                    is_saturday = random_date.weekday() == 5
                    is_sunday = random_date.weekday() == 6
                    is_holiday = is_public_holiday(random_date.strftime("%Y-%m-%d"))
                    
                    # Skip if day type doesn't match
                    day_type_lower = day_type_name.lower()
                    if day_type_lower == "weekday" and not is_weekday:
                        continue
                    elif day_type_lower == "saturday" and not is_saturday:
                        continue
                    elif day_type_lower == "sunday" and not is_sunday:
                        continue
                    elif day_type_lower == "holiday" and not is_holiday:
                        continue
                    
                    # For non-weekday trips, generate as private trips
                    is_private = day_type_name.lower() in ["saturday", "sunday", "holiday"]
                    new_trips = generate_sample_trips(
                        1, random_date, is_private, selected_vehicles
                    )
                    if new_trips:
                        trips.extend(new_trips)
                        total_distance += new_trips[0].get("totalDistanceKm", 0) or 0
                except ValueError:
                    pass  # Skip invalid dates

        elif total_distance > upper_bound:
            # Need to remove trips
            distance_over = total_distance - upper_bound
            print(
                f"[adjust_trips] {day_type_name} {month_key}: above target by {distance_over}, removing trips"
            )

            while total_distance > upper_bound and trips:
                removed_trip = trips.pop(random.randint(0, len(trips) - 1))
                total_distance -= removed_trip.get("totalDistanceKm", 0) or 0

        return trips

    # Now validate and adjust trips by month

    # Process weekday trips by month
    for month_key, trips in weekday_trips_by_month.items():
        adjusted_trips = adjust_trips_to_target(
            trips, weekday_avg_distance_per_month, "Weekday", month_key
        )
        for trip in adjusted_trips:
            _insert_trip_db_with_odometer_update(trip)
            all_trips.append(trip)

    # Process Saturday trips by month
    for month_key, trips in saturday_trips_by_month.items():
        adjusted_trips = adjust_trips_to_target(
            trips, saturday_avg_distance_per_month, "Saturday", month_key
        )
        for trip in adjusted_trips:
            _insert_trip_db_with_odometer_update(trip)
            all_trips.append(trip)

    # Process Sunday trips by month
    for month_key, trips in sunday_trips_by_month.items():
        adjusted_trips = adjust_trips_to_target(
            trips, sunday_avg_distance_per_month, "Sunday", month_key
        )
        for trip in adjusted_trips:
            _insert_trip_db_with_odometer_update(trip)
            all_trips.append(trip)

    # Process holiday trips by month
    for month_key, trips in holiday_trips_by_month.items():
        adjusted_trips = adjust_trips_to_target(
            trips, holiday_avg_distance_per_month, "Holiday", month_key
        )
        for trip in adjusted_trips:
            _insert_trip_db_with_odometer_update(trip)
            all_trips.append(trip)

    # Apply odometer readings with the provided starting value
    if all_trips:
        emit_progress(
            "applying_odometer_readings",
            {"totalTrips": len(all_trips)},
            progress_callback,
        )
        apply_odometer_readings(all_trips, start_reading=start_odometer_reading)

    emit_progress(
        "completed",
        {
            "totalTrips": len(all_trips),
            "message": "Sample data seeding completed successfully",
        },
        progress_callback,
    )



def emit_progress(step: str, details: dict = None, progress_callback=None):
    """Emit progress update via callback."""
    if progress_callback:
        try:
            progress_callback(step, details or {})
        except Exception as e:
            print(f"[emit_progress] Error emitting progress: {e}")
    print(f"[emit_progress] {step}: {details or {}}")


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def export_to_csv(filename="trips.csv"):
    trips = load_trips()
    fieldnames = [
        "date",
        "vehicleRegNumber",
        "client",
        "distanceKm",
        "tripType",
        "totalDistanceKm",
        "odometerStart",
        "odometerEnd",
    ]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trips)


# ---------------------------------------------------------------------------
# Public holidays CSV export/import
# ---------------------------------------------------------------------------
def export_public_holidays(filename="public_holidays.csv"):
    """Export all public holidays to a CSV file."""
    for db in get_db():
        holidays = db.query(PublicHoliday).order_by(PublicHoliday.date).all()
        fieldnames = ["date", "name", "country", "year"]
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for h in holidays:
                writer.writerow({
                    "date": h.date,
                    "name": h.name,
                    "country": h.country,
                    "year": h.year,
                })


def import_public_holidays(filename="public_holidays.csv"):
    """Import public holidays from a CSV file."""
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        holidays = [row for row in reader]
    import_holidays(holidays)


def startup():
    init_db()



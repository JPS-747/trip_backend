import json
from typing import Optional, List
import threading
import queue
import asyncio
import traceback
import logging

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import app


app.startup()


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("trippen")

# Global variable to track active WebSocket connection and progress queue for seeding
_seeding_websocket = None
_seeding_lock = threading.Lock()
_progress_queue = queue.Queue()  # Thread-safe queue for progress messages


class ClientCreate(BaseModel):
    client: str = Field(..., examples=["AB Company"])
    distanceFromOffice: float = Field(0.0, ge=0, examples=[12.5])
    fullAddress: Optional[str] = Field(
        None,
        examples=["1 Sandton Drive, Sandton, Johannesburg, Gauteng, South Africa"],
    )
    isDisabled: bool = Field(False, examples=[False])
    phoneNumber: Optional[str] = Field(None, examples=["+27 11 555 1234"])
    email: Optional[str] = Field(None, examples=["contact@company.com"])
    contactPerson: Optional[str] = Field(None, examples=["John Smith"])
    city: Optional[str] = Field(None, examples=["Johannesburg"])


class ClientStatusUpdate(BaseModel):
    isDisabled: bool = Field(..., examples=[True])


class VehicleCreate(BaseModel):
    regNumber: str = Field(..., examples=["ABC 123 GP"])
    make: str = Field(..., examples=["Toyota"])
    model: str = Field(..., examples=["Corolla"])
    year: Optional[int] = Field(None, examples=[2020])
    kmPerLiter: float = Field(0.0, ge=0, examples=[7.5])
    currentOdometer: Optional[float] = Field(None, ge=0, examples=[12345.6])
    ratePerKm: Optional[float] = Field(None, ge=0, examples=[4.50])
    isDisabled: bool = Field(False, examples=[False])


class VehicleStatusUpdate(BaseModel):
    isDisabled: bool = Field(..., examples=[True])


class HolidayCreate(BaseModel):
    date: str = Field(..., examples=["2026-03-21"])
    name: str = Field(..., examples=["Human Rights Day"])
    country: str = Field("South Africa", examples=["South Africa"])
    year: Optional[int] = None


class TripCreate(BaseModel):
    date: str = Field(..., examples=["2026-03-21"])
    client: Optional[str] = Field(None, examples=["AB Company"])
    city: Optional[str] = Field(None, examples=["Johannesburg"])
    distanceKm: float = Field(..., gt=0, examples=[12.5])
    tripType: int = Field(..., ge=0, le=2, examples=[1])
    isPrivateTrip: bool = Field(False, examples=[False])
    vehicleRegNumber: Optional[str] = Field(None, examples=["ABC 123 GP"])


class OdometerSetting(BaseModel):
    startingOdometer: float = Field(0.0, ge=0, examples=[12345.6])


class SeedRequest(BaseModel):
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    weekdayMinTripsPerDay: int = Field(0, ge=0, le=50)
    weekdayMaxTripsPerDay: int = Field(7, ge=0, le=50)
    weekdayAvgDistancePerMonth: Optional[float] = Field(None, ge=0)
    saturdayMinTripsPerDay: int = Field(0, ge=0, le=50)
    saturdayMaxTripsPerDay: int = Field(2, ge=0, le=50)
    saturdayAvgDistancePerMonth: Optional[float] = Field(None, ge=0)
    sundayMinTripsPerDay: int = Field(0, ge=0, le=50)
    sundayMaxTripsPerDay: int = Field(1, ge=0, le=50)
    sundayAvgDistancePerMonth: Optional[float] = Field(None, ge=0)
    holidayMinTripsPerDay: int = Field(0, ge=0, le=50)
    holidayMaxTripsPerDay: int = Field(3, ge=0, le=50)
    holidayAvgDistancePerMonth: Optional[float] = Field(None, ge=0)
    useSeasonalMultiplier: bool = Field(True, examples=[True])
    seasonalPeakMonth: float = Field(5.5, ge=0, le=11, examples=[5.5])
    seasonalSpread: float = Field(1.8, gt=0, le=6, examples=[1.8])
    selectedVehicles: Optional[List[str]] = Field(
        None, examples=[["ABC 123 GP", "XYZ 789 GP"]]
    )


def set_seeding_websocket(ws):
    """Set the active WebSocket for seeding progress updates."""
    global _seeding_websocket
    with _seeding_lock:
        _seeding_websocket = ws


def get_seeding_websocket():
    """Get the active WebSocket for seeding progress updates."""
    global _seeding_websocket
    with _seeding_lock:
        return _seeding_websocket


def queue_progress(message_type: str, data: dict):
    """Queue a progress message to be sent via WebSocket."""
    _progress_queue.put({"type": message_type, "data": data})


api = FastAPI(
    title="Trippen API",
    version="1.0.0",
    description="FastAPI interface for trip records, clients, public holidays, and CSV export.",
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tripfrontend-production.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/")
def root():
    return {
        "message": "Trippen API is running",
        "docs": "/docs",
        "endpoints": [
            "/trips",
            "/clients",
            "/holidays",
            "/seed-sample-data",
            "/export-csv",
        ],
    }


@api.websocket("/ws/seed-progress")
async def websocket_seed_progress(websocket: WebSocket):
    # Log handshake details before accepting
    logger.info("Handshake request path: %s", websocket.url.path)
    logger.info("Handshake headers: %s", dict(websocket.headers))

    await websocket.accept()
    set_seeding_websocket(websocket)
    logger.info("[WebSocket] Client connected for seed progress")

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                if data == "cancel":
                    logger.info("[WebSocket] Seeding cancellation requested")
                    break
            except asyncio.TimeoutError:
                pass

            try:
                while True:
                    message = _progress_queue.get_nowait()
                    await websocket.send_json(message)
            except queue.Empty:
                pass

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected")

    except Exception as e:
        logger.error("Unexpected error in WebSocket: %s", e)
        logger.error(traceback.format_exc())

    finally:
        set_seeding_websocket(None)


@api.get("/trips")
def get_trips(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=10000),
    client: Optional[str] = None,
    dayType: Optional[str] = None,
    sortBy: str = Query("date"),
    sortOrder: str = Query("asc"),
):
    return app.filter_sort_paginate_trips(
        page=page,
        page_size=pageSize,
        client=client,
        day_type=dayType,
        sort_by=sortBy,
        sort_order=sortOrder,
    )


@api.post("/trips")
def create_trip(payload: TripCreate):
    try:
        # Calculate total distance based on trip type multiplier
        total_distance = payload.distanceKm * payload.tripType
        print(payload)

        new_trip = app.create_trip_record(
            date=payload.date,
            client=payload.client or "",
            city=payload.city or "",
            distance_km=payload.distanceKm,
            total_distance_km=total_distance,
            trip_type=payload.tripType,
            is_private_trip=payload.isPrivateTrip,
            vehicle_reg_number=payload.vehicleRegNumber,
        )

        # Only upsert client if client is provided
        if payload.client and payload.client.strip():
            app.upsert_client(
                payload.client,
                distance_from_office=payload.distanceKm,
                full_address=payload.fullAddress,
            )

        return new_trip
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api.get("/trips/{trip_id}")
def get_trip_detail(trip_id: int):
    trip = app.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")
    return trip


@api.put("/trips/{trip_id}")
def update_trip(trip_id: int, payload: TripCreate):
    try:
        # Calculate total distance based on trip type multiplier
        total_distance = payload.distanceKm * payload.tripType
        print(payload)
        updated_trip = app.update_trip_record(
            trip_id,
            date=payload.date,
            client=payload.client or "",
            city=payload.city or "",
            distance_km=payload.distanceKm,
            total_distance_km=total_distance,
            trip_type=payload.tripType,
            is_private_trip=payload.isPrivateTrip,
            vehicle_reg_number=payload.vehicleRegNumber,
        )
        if not updated_trip:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")

        if payload.client and payload.client.strip():
            app.upsert_client(
                payload.client,
                distance_from_office=payload.distanceKm,
                city=payload.city,
            )

        return updated_trip
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api.delete("/trips/{trip_id}")
def delete_trip(trip_id: int):
    deleted = app.delete_trip_record(trip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found")
    return {"message": f"Trip '{trip_id}' deleted successfully"}


@api.get("/clients")
def get_clients(
    page: int = 1, pageSize: int = 10, sortBy: str = "client", sortOrder: str = "asc"
):
    return app.filter_sort_paginate_clients(
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_order=sortOrder,
    )


@api.post("/clients", status_code=201)
def create_client(payload: ClientCreate):
    app.upsert_client(
        client=payload.client,
        city=payload.city,
        distance_from_office=payload.distanceFromOffice,
        full_address=payload.fullAddress,
        is_disabled=payload.isDisabled,
        phone_number=payload.phoneNumber,
        email=payload.email,
        contact_person=payload.contactPerson,
    )
    return app.filter_sort_paginate_clients()


@api.delete("/clients/{client_name}")
def delete_client(client_name: str):
    deleted = app.delete_client(client_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found")
    return {"message": f"Client '{client_name}' deleted successfully"}


@api.patch("/clients/{client_name}/status")
def update_client_status(client_name: str, payload: ClientStatusUpdate):
    updated = app.set_client_disabled(client_name, payload.isDisabled)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found")
    return {
        "client": client_name,
        "isDisabled": payload.isDisabled,
        "clients": app.load_clients(),
    }


@api.post("/clients/import")
def import_clients(clients: List[ClientCreate]):
    print("[clients/import] Received payload:")
    print(json.dumps([c.model_dump() for c in clients], indent=2))
    records = [
        {
            "client": c.client,
            "distanceFromOffice": c.distanceFromOffice,
            "fullAddress": c.fullAddress or "",
            "isDisabled": c.isDisabled,
            "phoneNumber": c.phoneNumber,
            "email": c.email,
            "contactPerson": c.contactPerson,
            "city": c.city,
        }
        for c in clients
    ]
    count = app.import_clients(records)
    return {"message": f"{count} client(s) imported", "clients": app.load_clients()}


@api.get("/vehicles")
def get_vehicles():
    return app.load_vehicles()


@api.post("/vehicles", status_code=201)
def create_vehicle(payload: VehicleCreate):
    app.upsert_vehicle(
        reg_number=payload.regNumber,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        km_per_liter=payload.kmPerLiter,
        current_odometer=payload.currentOdometer,
        rate_per_km=payload.ratePerKm,
        is_disabled=payload.isDisabled,
    )
    return app.load_vehicles()


@api.delete("/vehicles/{reg_number}")
def delete_vehicle(reg_number: str):
    deleted = app.delete_vehicle(reg_number)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Vehicle '{reg_number}' not found")
    return {"message": f"Vehicle '{reg_number}' deleted successfully"}


@api.patch("/vehicles/{reg_number}/status")
def update_vehicle_status(reg_number: str, payload: VehicleStatusUpdate):
    updated = app.set_vehicle_disabled(reg_number, payload.isDisabled)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Vehicle '{reg_number}' not found")
    return {
        "regNumber": reg_number,
        "isDisabled": payload.isDisabled,
        "vehicles": app.load_vehicles(),
    }


@api.get("/holidays")
def get_holidays():
    return app.load_public_holidays()


@api.post("/holidays", status_code=201)
def create_holiday(payload: HolidayCreate):
    app.add_holiday(
        date=payload.date,
        name=payload.name,
        country=payload.country,
        year=payload.year,
    )
    return app.load_public_holidays()


@api.delete("/holidays")
def delete_holiday(date: str, name: str):
    deleted = app.delete_holiday(date, name)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Holiday '{name}' on {date} not found"
        )
    return {"message": f"Holiday '{name}' on {date} deleted successfully"}


@api.post("/holidays/import")
def import_holidays(holidays: List[HolidayCreate]):
    records = [
        {
            "date": h.date,
            "name": h.name,
            "country": h.country,
            "year": h.year,
        }
        for h in holidays
    ]
    count = app.import_holidays(records)
    return {
        "message": f"{count} holiday(s) imported",
        "holidays": app.load_public_holidays(),
    }

@api.get("/holidays/export")
def export_public_holidays():
    app.export_public_holidays()
    return FileResponse("public_holidays.csv", media_type="text/csv", filename="public_holidays.csv")



@api.post("/seed-sample-data")
def seed_sample_data(payload: Optional[SeedRequest] = None):
    seed_options = payload or SeedRequest()
    print(f"[seed_sample_data] Received payload: {seed_options.model_dump()}")
    print(f"[seed_sample_data] selectedVehicles = {seed_options.selectedVehicles}")

    # Define a progress callback that queues updates for WebSocket
    def on_progress(step: str, details: dict):
        """Callback to queue progress updates for the WebSocket client."""
        queue_progress(step, details)

    app.add_sample_data(
        start_date=seed_options.startDate,
        end_date=seed_options.endDate,
        weekday_min_trips_per_day=seed_options.weekdayMinTripsPerDay,
        weekday_max_trips_per_day=seed_options.weekdayMaxTripsPerDay,
        weekday_avg_distance_per_month=seed_options.weekdayAvgDistancePerMonth,
        saturday_min_trips_per_day=seed_options.saturdayMinTripsPerDay,
        saturday_max_trips_per_day=seed_options.saturdayMaxTripsPerDay,
        saturday_avg_distance_per_month=seed_options.saturdayAvgDistancePerMonth,
        sunday_min_trips_per_day=seed_options.sundayMinTripsPerDay,
        sunday_max_trips_per_day=seed_options.sundayMaxTripsPerDay,
        sunday_avg_distance_per_month=seed_options.sundayAvgDistancePerMonth,
        holiday_min_trips_per_day=seed_options.holidayMinTripsPerDay,
        holiday_max_trips_per_day=seed_options.holidayMaxTripsPerDay,
        holiday_avg_distance_per_month=seed_options.holidayAvgDistancePerMonth,
        use_seasonal_multiplier=seed_options.useSeasonalMultiplier,
        seasonal_peak_month=seed_options.seasonalPeakMonth,
        seasonal_spread=seed_options.seasonalSpread,
        selected_vehicles=seed_options.selectedVehicles,
        progress_callback=on_progress,
    )
    print(f"Sample data seeded with options: {seed_options.model_dump()}")
    return {
        "message": "Sample data seeding started",
        "tripCount": len(app.load_trips()),
    }


@api.post("/export-csv")
def export_csv():
    app.export_to_csv()
    return {
        "message": "CSV exported successfully",
        "file": app.TRIPS_FILE.replace("trips.json", "trips.csv"),
    }


@api.get("/download-csv")
def download_csv():
    app.export_to_csv()
    return FileResponse("trips.csv", media_type="text/csv", filename="trips.csv")


@api.post("/cleanup-trips")
def cleanup_trips():
    cleaned_trips = app.cleanup_trips_data()
    return {
        "message": "Trips cleaned successfully",
        "tripCount": len(cleaned_trips),
    }


@api.post("/clear-trips")
def clear_trips(startDate: str | None = None, endDate: str | None = None):
    print(f"DEBUG API: Received startDate={startDate}, endDate={endDate}")
    trip_count = app.clear_trips_data(startDate, endDate)
    print(f"DEBUG API: Deleted {trip_count} trips")
    return {
        "message": "Trips cleared successfully",
        "tripCount": trip_count,
    }


@api.post("/clear-clients")
def clear_clients():
    app.clear_clients_data()
    return {
        "message": "Clients cleared successfully",
        "clientCount": 0,
    }


@api.post("/clear-holidays")
def clear_holidays():
    app.clear_holidays_data()
    return {
        "message": "Holidays cleared successfully",
        "holidayCount": 0,
    }


@api.patch("/holidays")
def patch_holidays(holidays: List[HolidayCreate] = Body(...)):
    """
    Patch (bulk update) public holidays. Each record must include date and name as keys.
    If a holiday exists (by date and name), it will be updated; otherwise, it will be created.
    """
    updated = 0
    created = 0
    for h in holidays:
        # Try to update existing holiday
        found = False
        for db in app.get_db():
            obj = db.query(app.PublicHoliday).filter(app.PublicHoliday.date == h.date, app.PublicHoliday.name == h.name).first()
            if obj:
                obj.country = h.country
                obj.year = h.year
                db.commit()
                updated += 1
                found = True
                break
        if not found:
            app.add_holiday(h.date, h.name, h.country, h.year)
            created += 1
    return {
        "message": f"{updated} holiday(s) updated, {created} created",
        "updated": updated,
        "created": created,
        "holidays": app.load_public_holidays(),
    }




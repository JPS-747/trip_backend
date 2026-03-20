import app

app.startup()

# Check the starting odometer
starting_odometer = app.get_starting_odometer()
print(f"Starting odometer: {starting_odometer}")

# Load trips
trips = app.load_trips()
print(f"Total trips: {len(trips)}")

# Show first few trips
for trip in trips[:3]:
    print(
        f"  ID {trip.get('id')}: {trip.get('totalDistanceKm')} km, odometerEnd={trip.get('odometerEnd')}"
    )

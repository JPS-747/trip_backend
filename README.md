# Trippen - Trip Tracking System

A sophisticated trip-tracking application with a FastAPI backend and React TypeScript frontend. Manage vehicle trips, track distances, calculate costs, and generate detailed reports with real-time progress notifications.

## 🎯 Features

### Backend

- **Trip Management**: Create, read, update, and delete trips with complete trip data
- **Client Management**: Store and manage client information with city assignment
- **Vehicle Tracking**: Track vehicles with odometer readings and cost calculations
- **Public Holidays**: Support for public holiday lookups and special day handling
- **Smart Data Seeding**: Intelligent sample data generation with:
  - Seasonal multipliers (peak distance in Aug-Sept)
  - Day-type awareness (weekday/Saturday/Sunday/holiday)
  - Distance targeting with ±10% tolerance bands
  - Automatic trip adjustment to meet distance targets
  - Real-time WebSocket progress notifications
- **CSV Export**: Export all trip data to CSV format
- **SQLite Database**: Persistent data storage with migration support

### Frontend

- **React 18 + TypeScript**: Modern, type-safe UI components
- **Responsive Dashboard**: View all trips and clients with filtering
- **Real-time Progress**: Live progress updates during data seeding via WebSocket
- **Pagination & Sorting**: Efficient data browsing with multiple sort options
- **Trip Management UI**: Full CRUD operations for trips and clients
- **Odometer Tracking**: Visual display of vehicle odometer readings

## 📋 API Endpoints

### Trips

- `GET /trips` - List all trips with pagination and filtering
- `POST /trips` - Create a new trip
- `GET /trips/{id}` - Get a specific trip
- `PUT /trips/{id}` - Update a trip
- `DELETE /trips/{id}` - Delete a trip

### Clients

- `GET /clients` - List all clients
- `POST /clients` - Create a new client
- `GET /clients/{name}` - Get a specific client
- `PUT /clients/{name}` - Update a client
- `DELETE /clients/{name}` - Delete a client

### Vehicles

- `GET /vehicles` - List all vehicles
- `POST /vehicles` - Create a new vehicle
- `GET /vehicles/{reg_number}` - Get a specific vehicle
- `PUT /vehicles/{reg_number}` - Update a vehicle
- `DELETE /vehicles/{reg_number}` - Delete a vehicle

### Data & Export

- `GET /holidays` - Get public holidays data
- `POST /holidays` - Add a new holiday
- `POST /seed-sample-data` - Generate sample data with real-time progress
- `GET /export-csv` - Export trips to CSV
- `GET /download-csv` - Download the CSV file
- `WebSocket /ws/seed-progress` - Real-time seeding progress updates

### Documentation

- `GET /` - API summary
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Create and activate a virtual environment:

```powershell
python -m venv v310
& .\v310\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the API server:

```powershell
uvicorn api:api --reload
```

The API will be available at `http://127.0.0.1:8000`

### Frontend Setup

1. Navigate to the frontend directory:

```powershell
cd frontend-react
```

2. Install npm dependencies:

```powershell
npm install
```

3. Start the development server:

```powershell
npm run dev
```

The frontend will be available at `http://127.0.0.1:5173`

### Accessing the Application

- **API Documentation**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Frontend Dashboard**: http://127.0.0.1:5173

## 📊 Sample Data Generation

The system includes intelligent sample data generation with the following parameters:

```json
POST /seed-sample-data
{
  "start_date": "2026-03-01",
  "end_date": "2026-05-31",
  "weekday_min_trips_per_day": 1,
  "weekday_max_trips_per_day": 3,
  "weekday_avg_distance_per_month": 1500,
  "saturday_min_trips_per_day": 0,
  "saturday_max_trips_per_day": 2,
  "saturday_avg_distance_per_month": 500,
  "sunday_min_trips_per_day": 0,
  "sunday_max_trips_per_day": 1,
  "sunday_avg_distance_per_month": 200,
  "holiday_min_trips_per_day": 0,
  "holiday_max_trips_per_day": 3,
  "holiday_avg_distance_per_month": 300,
  "use_seasonal_multiplier": true,
  "seasonal_peak_month": 5.5,
  "seasonal_spread": 1.8,
  "selected_vehicles": ["ZN21ABC"]
}
```

### Real-time Progress Updates

The seeding process emits real-time progress updates via WebSocket:

1. **initialized** - Seeding started with parameters
2. **generating\_\*\_trips** - Trip generation for day type started
3. **\*\_trips_generated** - Day type trip generation completed
4. **adjusting\_\*\_distance** - Distance adjustment for day type with current metrics
5. **applying_odometer_readings** - Final odometer calculation
6. **completed** - Seeding finished successfully

## 🏗️ Project Structure

```
trippen/
├── api.py                      # FastAPI application & WebSocket endpoints
├── app.py                      # Core business logic & data management
├── db.py                       # Database initialization & context manager
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # This file
│
├── frontend-react/             # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── App.tsx            # Main app component
│   │   ├── main.tsx           # Entry point
│   │   └── index.css          # Styles
│   ├── package.json           # npm dependencies
│   ├── vite.config.ts         # Vite configuration
│   └── tsconfig.json          # TypeScript configuration
│
├── clients.json                # Client data (will be migrated to DB)
├── public_holidays.json        # Public holidays data
├── trippen.db                  # SQLite database (gitignored)
│
├── Migration Scripts/          # Database migration utilities
│   ├── migrate_add_city_columns_in_trips.py
│   ├── migrate_add_client_columns.py
│   ├── migrate_update_clients_city.py
│   └── insert_namibia_holidays.py
│
└── Test & Debug Scripts/       # Development utilities (gitignored)
    ├── check_db.py
    ├── debug_trips.py
    └── test_*.py
```

## 🔧 Technology Stack

### Backend

- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI web server
- **SQLite** - Lightweight relational database
- **WebSockets** - Real-time progress communication
- **Pydantic** - Data validation and serialization

### Frontend

- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **React Router** - Client-side routing
- **WebSocket API** - Real-time updates

## 📈 Key Features in Detail

### Distance Targeting

The system uses intelligent distance targeting to ensure realistic trip data:

- Sets target average distance per month for each day type
- Automatically adds or removes trips to stay within ±10% tolerance
- Respects day-type constraints (weekday vs weekend vs holiday)
- Prevents cross-contamination of different day types

### Seasonal Multipliers

Trip generation includes seasonal variation:

- Peak season: August-September (financial year month 5-6)
- Configurable peak month and spread
- Multiplier range: 0.5x to 1.5x of base trip counts
- Realistic simulation of seasonal business variations

### Odometer Tracking

Each vehicle maintains accurate odometer readings:

- Starting odometer value per vehicle
- Per-trip odometer tracking
- Automatic updates when trips are added/removed
- Support for both vehicle-assigned and unassigned trips

### Private Trips

Support for private (non-client) trips:

- Random distances (3-10 km)
- Weekend and holiday trips default to private
- No city-based client logic applied
- Useful for operational/maintenance journeys

## 🔐 Security Considerations

- SQLite database not committed to version control
- Environment variables support for sensitive config (future enhancement)
- Input validation via Pydantic models
- CORS headers configurable in api.py

## 📝 Example Workflows

### Create a Trip

```powershell
$body = @{
    date = "2026-03-21"
    client = "Demo Client"
    city = "Windhoek"
    distance_km = 10.5
    trip_type = 2
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/trips `
  -ContentType 'application/json' -Body $body
```

### Export and Download Trips

```powershell
# Trigger export
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/export-csv

# Download the file
Invoke-WebRequest -Uri http://127.0.0.1:8000/download-csv `
  -OutFile trips.csv
```

### Monitor Seeding Progress

```javascript
// In browser console
const ws = new WebSocket("ws://127.0.0.1:8000/ws/seed-progress");
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message.details);
};
```

## 🐛 Troubleshooting

### Database Issues

If you encounter database issues:

1. Check existing tables: `python check_db.py`
2. Run migrations: Individual migration scripts can be executed
3. Reset database: Delete `trippen.db` and restart the server

### Frontend Not Connecting

- Verify API server is running on `http://127.0.0.1:8000`
- Check browser console for WebSocket connection errors
- Ensure CORS is enabled in `api.py`

### Port Already in Use

- Change API port: `uvicorn api:api --port 8001`
- Change frontend port: `npm run dev -- --port 5174`

## 📚 Additional Documentation

- See `CLIENT_ENHANCEMENT_SUMMARY.md` for recent feature additions
- API documentation available at `http://127.0.0.1:8000/docs`
- Check migration scripts for database schema details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Created as a vehicle trip management system for tracking distances, clients, and costs.

## 🙋 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Last Updated**: March 2026

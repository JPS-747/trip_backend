# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Real-time WebSocket progress notifications for data seeding
- Day-type aware trip adjustment in distance targeting
- Support for private trips (weekend/holiday operations)
- SQLite database migration system
- React TypeScript frontend with modern UI

### Changed

- Refactored progress system to use callbacks
- Database now primary storage (JSON files for reference)
- Improved odometer tracking per-vehicle

### Fixed

- Missing city field in trip records causing KeyErrors
- Distance calculations now respect day-type boundaries
- Popup auto-close behavior in frontend

## [1.0.0] - 2026-03-20

### Initial Release

#### Backend Features

- FastAPI REST API for trip management
- SQLite database with automatic migrations
- Client and vehicle management
- Public holiday support
- Intelligent sample data generation with:
  - Seasonal multipliers
  - Distance targeting with ±10% tolerance
  - Day-type awareness (weekday/weekend/holiday)
  - Real-time progress via WebSocket

#### Frontend Features

- React 18 TypeScript dashboard
- Trip and client management UI
- Real-time progress notifications
- CSV export functionality
- Pagination and sorting

#### API Endpoints

- `/trips` - Full CRUD operations
- `/clients` - Client management
- `/vehicles` - Vehicle tracking
- `/holidays` - Holiday management
- `/seed-sample-data` - Intelligent data generation
- `/export-csv` - Data export
- `/ws/seed-progress` - Real-time updates

#### Documentation

- Comprehensive README
- API documentation via Swagger UI
- Contributing guidelines
- Database migration scripts

### Technical Stack

- **Backend**: FastAPI, Uvicorn, SQLite, WebSockets, Pydantic
- **Frontend**: React 18, TypeScript, Vite
- **Database**: SQLite with migration support
- **Development**: Python 3.10+, Node.js 16+

---

## Version History

### Development Notes

#### Recent Improvements (Pre-1.0)

1. **Smart Distance Targeting**

   - Automatic trip adjustment to meet distance targets
   - ±10% tolerance bands per day type
   - Prevents cross-contamination between day types

2. **Progress System**

   - Unified emit_progress callback mechanism
   - Real-time WebSocket notifications
   - 12-step seeding progress tracking

3. **Database Stability**

   - Context manager pattern for connections
   - Automatic migration system
   - City field standardization

4. **Frontend Enhancements**
   - Disabled auto-close on seeding completion
   - Real-time progress display
   - Responsive component design

### Known Limitations

- Single-file SQLite database (suitable for small-to-medium datasets)
- No user authentication (future enhancement)
- No backup/restore functionality (future enhancement)
- Local-only deployment (no cloud support yet)

### Future Roadmap

- [ ] User authentication and multi-user support
- [ ] Database backup and restore functionality
- [ ] Advanced reporting and analytics
- [ ] API rate limiting and throttling
- [ ] Docker containerization
- [ ] Cloud deployment support
- [ ] Mobile app companion
- [ ] Offline capability for frontend
- [ ] Export to Excel with formatting
- [ ] Scheduled automatic backups

### Migration from Legacy Versions

- JSON files automatically migrated to SQLite on first run
- All existing data preserved during migration
- Backward compatibility maintained for imports

---

**Last Updated**: March 20, 2026
